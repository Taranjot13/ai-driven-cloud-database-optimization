import re
import statistics
import psycopg2


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "cloud_optimizer",
    "user": "postgres",
    "password": "123456t"
}


WARMUP_RUNS = 3
MEASUREMENT_RUNS = 7
EXECUTIONS_PER_SAMPLE = 10

MAX_MAD_VARIATION_PERCENT = 25.0
OUTLIER_MAD_MULTIPLIER = 3.0
MIN_PRACTICAL_TIMING_MS = 0.20

IMPROVEMENT_THRESHOLD = 5.0


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def validate_query(query):
    """
    Allow only read-only SELECT/WITH queries.
    """

    cleaned = query.strip()

    if not re.match(
        r"^(SELECT|WITH)\b",
        cleaned,
        re.IGNORECASE
    ):
        raise ValueError(
            "Only SELECT and WITH queries are allowed."
        )


def normalize_query(query):
    """
    Replace parameter placeholders with a safe
    representative value for execution.
    """

    normalized = re.sub(
        r"%s",
        "5000",
        query
    )

    normalized = re.sub(
        r"\$\d+",
        "5000",
        normalized
    )

    return normalized


def build_index_name(
    table_name,
    filter_column,
    order_column
):
    """
    Generate a predictable composite-index name.
    """

    return (
        f"idx_{table_name}_"
        f"{filter_column}_"
        f"{order_column}_composite"
    )


def validate_identifier(identifier):
    """
    Validate SQL identifiers before they are inserted
    into DDL statements.
    """

    if not re.match(
        r"^[a-zA-Z_][a-zA-Z0-9_]*$",
        identifier
    ):
        raise ValueError(
            f"Unsafe SQL identifier: {identifier}"
        )


def execute_query(
    connection,
    query
):
    """
    Execute the query and measure elapsed time.
    """

    cursor = connection.cursor()

    start_time = None
    end_time = None

    try:
        cursor.execute(
            "SELECT clock_timestamp();"
        )

        start_time = cursor.fetchone()[0]

        cursor.execute(query)

        if cursor.description is not None:
            cursor.fetchall()

        cursor.execute(
            "SELECT clock_timestamp();"
        )

        end_time = cursor.fetchone()[0]

    finally:
        cursor.close()

    elapsed_ms = (
        end_time - start_time
    ).total_seconds() * 1000

    return elapsed_ms


def measure_query(
    connection,
    query,
    label
):
    """
    Perform warm-up and repeated measurements.

    Returns robust statistics using median,
    MAD, outlier detection and stability.
    """

    print(
        f"\nRunning {WARMUP_RUNS} "
        f"warm-up executions..."
    )

    for _ in range(WARMUP_RUNS):

        execute_query(
            connection,
            query
        )

    print(
        "Warm-up completed."
    )

    print(
        f"\nCollecting {MEASUREMENT_RUNS} "
        f"measurement samples..."
    )

    print(
        f"Each sample executes the query "
        f"{EXECUTIONS_PER_SAMPLE} times."
    )

    samples = []

    for sample_number in range(
        1,
        MEASUREMENT_RUNS + 1
    ):

        executions = []

        for _ in range(
            EXECUTIONS_PER_SAMPLE
        ):

            elapsed = execute_query(
                connection,
                query
            )

            executions.append(
                elapsed
            )

        sample_average = statistics.mean(
            executions
        )

        samples.append(
            sample_average
        )

        print(
            f"Sample {sample_number}: "
            f"{sample_average:.3f} ms"
        )

    median_value = statistics.median(
        samples
    )

    deviations = [
        abs(
            value - median_value
        )
        for value in samples
    ]

    mad = statistics.median(
        deviations
    )

    denominator = max(
        median_value,
        MIN_PRACTICAL_TIMING_MS
    )

    robust_variation = (
        mad / denominator
    ) * 100

    lower_bound = (
        median_value
        - OUTLIER_MAD_MULTIPLIER * mad
    )

    upper_bound = (
        median_value
        + OUTLIER_MAD_MULTIPLIER * mad
    )

    outliers = [
        value
        for value in samples
        if (
            value < lower_bound
            or value > upper_bound
        )
    ]

    stable = (
        robust_variation
        <= MAX_MAD_VARIATION_PERCENT
    )

    print(
        f"\n===== {label.upper()} MEASUREMENT ====="
    )

    print(
        "Measurement samples: "
        + ", ".join(
            f"{value:.3f} ms"
            for value in samples
        )
    )

    print(
        f"Median: "
        f"{median_value:.3f} ms"
    )

    print(
        f"Minimum: "
        f"{min(samples):.3f} ms"
    )

    print(
        f"Maximum: "
        f"{max(samples):.3f} ms"
    )

    print(
        f"MAD: "
        f"{mad:.3f} ms"
    )

    print(
        f"Robust variation: "
        f"{robust_variation:.2f}%"
    )

    if outliers:

        print(
            "Detected timing outliers: "
            + ", ".join(
                f"{value:.3f} ms"
                for value in outliers
            )
        )

    else:

        print(
            "Detected timing outliers: None"
        )

    print(
        "Measurement stability: "
        + (
            "STABLE"
            if stable
            else "UNSTABLE"
        )
    )

    if median_value < MIN_PRACTICAL_TIMING_MS:

        print(
            "Measurement note: Execution time "
            "is below the practical timing threshold."
        )

    return {
        "samples": samples,
        "median_ms": median_value,
        "minimum_ms": min(samples),
        "maximum_ms": max(samples),
        "mad_ms": mad,
        "robust_variation_percent":
            robust_variation,
        "outliers": outliers,
        "stable": stable
    }


def index_exists(
    connection,
    index_name
):
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE indexname = %s
            );
            """,
            (index_name,)
        )

        return cursor.fetchone()[0]

    finally:

        cursor.close()


def create_composite_index(
    connection,
    table_name,
    filter_column,
    order_column,
    direction,
    index_name
):
    validate_identifier(
        table_name
    )

    validate_identifier(
        filter_column
    )

    validate_identifier(
        order_column
    )

    validate_identifier(
        index_name
    )

    direction = direction.upper()

    if direction not in {
        "ASC",
        "DESC"
    }:

        raise ValueError(
            "Invalid index sort direction."
        )

    sql = f"""
        CREATE INDEX {index_name}
        ON {table_name}
        (
            {filter_column},
            {order_column} {direction}
        );
    """

    cursor = connection.cursor()

    try:

        cursor.execute(sql)
        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        cursor.close()


def drop_index(
    connection,
    index_name
):
    validate_identifier(
        index_name
    )

    cursor = connection.cursor()

    try:

        cursor.execute(
            f"""
            DROP INDEX IF EXISTS {index_name};
            """
        )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        cursor.close()


def calculate_improvement(
    baseline_ms,
    optimized_ms
):
    """
    Calculate percentage performance improvement.
    """

    if baseline_ms <= 0:
        return 0.0

    return (
        (
            baseline_ms
            - optimized_ms
        )
        / baseline_ms
    ) * 100


def save_history(
    connection,
    metric_id,
    table_name,
    column_name,
    baseline_ms,
    optimized_ms,
    improvement_percent,
    decision
):
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO optimization_history (
                metric_id,
                optimization_type,
                table_name,
                column_name,
                baseline_time_ms,
                optimized_time_ms,
                improvement_percent,
                decision
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            );
            """,
            (
                metric_id,
                "COMPOSITE_INDEX",
                table_name,
                column_name,
                baseline_ms,
                optimized_ms,
                improvement_percent,
                decision
            )
        )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        cursor.close()


def verify_existing_index(
    connection,
    normalized_query,
    metric_id,
    table_name,
    filter_column,
    order_column,
    direction,
    index_name
):
    """
    Verify an existing composite index.

    Procedure:

    1. Existing indexed measurement
    2. Temporarily remove existing index
    3. Measure baseline without index
    4. Recreate the existing index
    5. Measure indexed performance again
    6. Compare robust statistics
    7. Preserve the index
    8. Save verification history

    The index is always restored after the baseline
    measurement, even if verification fails.
    """

    print(
        "\n===== EXISTING INDEX VERIFICATION ====="
    )

    print(
        "The composite index already exists."
    )

    print(
        f"Index: {index_name}"
    )

    print(
        "\nThe system will temporarily remove "
        "the index to establish a no-index baseline."
    )

    print(
        "The index will then be recreated and "
        "measured again."
    )

    # ---------------------------------------------
    # Current indexed measurement
    # ---------------------------------------------

    print(
        "\n[1/3] Measuring existing indexed state..."
    )

    existing_index_measurement = measure_query(
        connection,
        normalized_query,
        "existing indexed"
    )

    # ---------------------------------------------
    # Remove existing index
    # ---------------------------------------------

    print(
        "\n[2/3] Temporarily removing existing index..."
    )

    drop_index(
        connection,
        index_name
    )

    print(
        f"Temporarily removed: {index_name}"
    )

    baseline = None

    try:

        baseline = measure_query(
            connection,
            normalized_query,
            "no index baseline"
        )

    finally:

        # -----------------------------------------
        # ALWAYS RESTORE INDEX
        # -----------------------------------------

        print(
            "\nRestoring existing composite index..."
        )

        if not index_exists(
            connection,
            index_name
        ):

            create_composite_index(
                connection,
                table_name,
                filter_column,
                order_column,
                direction,
                index_name
            )

            print(
                f"Restored: {index_name}"
            )

    # ---------------------------------------------
    # Re-measure restored index
    # ---------------------------------------------

    print(
        "\n[3/3] Measuring restored indexed state..."
    )

    indexed = measure_query(
        connection,
        normalized_query,
        "restored indexed"
    )

    baseline_stable = baseline["stable"]
    indexed_stable = indexed["stable"]

    baseline_time = baseline["median_ms"]
    indexed_time = indexed["median_ms"]

    improvement = calculate_improvement(
        baseline_time,
        indexed_time
    )

    print(
        "\n===== EXISTING INDEX VERIFICATION RESULT ====="
    )

    print(
        f"No-index baseline median: "
        f"{baseline_time:.3f} ms"
    )

    print(
        f"Indexed median: "
        f"{indexed_time:.3f} ms"
    )

    print(
        f"Observed improvement: "
        f"{improvement:.2f}%"
    )

    print(
        "Baseline stable: "
        f"{'YES' if baseline_stable else 'NO'}"
    )

    print(
        "Indexed measurement stable: "
        f"{'YES' if indexed_stable else 'NO'}"
    )

    if (
        baseline_stable
        and indexed_stable
        and improvement >= IMPROVEMENT_THRESHOLD
    ):

        decision = (
            "EXISTING INDEX VERIFIED"
        )

        print(
            "\nDecision: "
            "EXISTING INDEX VERIFIED"
        )

        print(
            "The existing composite index provides "
            "a stable performance improvement."
        )

    elif (
        baseline_stable
        and indexed_stable
    ):

        decision = (
            "EXISTING INDEX NOT VERIFIED"
        )

        print(
            "\nDecision: "
            "EXISTING INDEX NOT VERIFIED"
        )

        print(
            f"The measured improvement is below "
            f"the {IMPROVEMENT_THRESHOLD:.1f}% "
            "verification threshold."
        )

        print(
            "The existing index is nevertheless "
            "preserved."
        )

    else:

        decision = (
            "MEASUREMENT UNSTABLE"
        )

        print(
            "\nDecision: MEASUREMENT UNSTABLE"
        )

        print(
            "The measurements were too variable "
            "for a confident conclusion."
        )

        print(
            "The existing index is preserved."
        )

    save_history(
        connection=connection,
        metric_id=metric_id,
        table_name=table_name,
        column_name=(
            f"{filter_column},"
            f"{order_column}"
        ),
        baseline_ms=baseline_time,
        optimized_ms=indexed_time,
        improvement_percent=improvement,
        decision=decision
    )

    print(
        "\nVerification result saved to history."
    )

    print(
        "Existing composite index preserved."
    )

    return {
        "decision": decision,
        "index_name": index_name,
        "baseline_time_ms": baseline_time,
        "optimized_time_ms": indexed_time,
        "improvement_percent": improvement
    }


def optimize_composite_index(
    metric_id,
    query_text,
    table_name,
    filter_column,
    order_column,
    direction="DESC"
):
    """
    Safely test or verify a composite index.

    Existing index:
        Verify actual performance benefit.

    Missing index:
        Measure baseline -> create index ->
        measure optimized -> keep or rollback.
    """

    validate_query(
        query_text
    )

    validate_identifier(
        table_name
    )

    validate_identifier(
        filter_column
    )

    validate_identifier(
        order_column
    )

    if direction.upper() not in {
        "ASC",
        "DESC"
    }:

        raise ValueError(
            "Invalid index sort direction."
        )

    normalized_query = normalize_query(
        query_text
    )

    index_name = build_index_name(
        table_name,
        filter_column,
        order_column
    )

    connection = get_connection()

    try:

        print(
            "\n"
            + "=" * 60
        )

        print(
            " AUTONOMOUS COMPOSITE INDEX OPTIMIZATION"
        )

        print(
            "=" * 60
        )

        print(
            f"Target: "
            f"{table_name}."
            f"{filter_column}, "
            f"{order_column} "
            f"{direction.upper()}"
        )

        print(
            f"Index: "
            f"{index_name}"
        )

        print(
            f"Warm-up runs: "
            f"{WARMUP_RUNS}"
        )

        print(
            f"Measurement samples: "
            f"{MEASUREMENT_RUNS}"
        )

        print(
            f"Executions per sample: "
            f"{EXECUTIONS_PER_SAMPLE}"
        )

        print(
            f"Maximum allowed robust variation: "
            f"{MAX_MAD_VARIATION_PERCENT:.1f}%"
        )

        print(
            f"Verification improvement threshold: "
            f"{IMPROVEMENT_THRESHOLD:.1f}%"
        )

        # =========================================
        # EXISTING INDEX PATH
        # =========================================

        if index_exists(
            connection,
            index_name
        ):

            return verify_existing_index(
                connection=connection,
                normalized_query=normalized_query,
                metric_id=metric_id,
                table_name=table_name,
                filter_column=filter_column,
                order_column=order_column,
                direction=direction,
                index_name=index_name
            )

        # =========================================
        # BASELINE
        # =========================================

        print(
            "\nNo composite index currently exists."
        )

        print(
            "\n===== BASELINE MEASUREMENT ====="
        )

        baseline = measure_query(
            connection,
            normalized_query,
            "baseline"
        )

        # =========================================
        # BASELINE SAFETY CHECK
        # =========================================

        if not baseline["stable"]:

            decision = (
                "ROLLBACK_UNSTABLE_BASELINE"
            )

            print(
                "\nDecision: "
                "ROLLBACK_UNSTABLE_BASELINE"
            )

            print(
                "Baseline measurements were too "
                "variable for a safe comparison."
            )

            save_history(
                connection,
                metric_id,
                table_name,
                (
                    f"{filter_column},"
                    f"{order_column}"
                ),
                baseline["median_ms"],
                None,
                None,
                decision
            )

            return {
                "decision": decision,
                "index_name": index_name,
                "baseline_time_ms":
                    baseline["median_ms"],
                "optimized_time_ms": None,
                "improvement_percent": None
            }

        # =========================================
        # CREATE CANDIDATE INDEX
        # =========================================

        print(
            "\nCreating candidate composite index..."
        )

        create_composite_index(
            connection,
            table_name,
            filter_column,
            order_column,
            direction,
            index_name
        )

        print(
            f"Created: {index_name}"
        )

        # =========================================
        # OPTIMIZED MEASUREMENT
        # =========================================

        optimized = measure_query(
            connection,
            normalized_query,
            "composite indexed"
        )

        # =========================================
        # OPTIMIZED STABILITY CHECK
        # =========================================

        if not optimized["stable"]:

            decision = (
                "ROLLBACK_UNSTABLE_OPTIMIZED"
            )

            print(
                "\nDecision: "
                "ROLLBACK_UNSTABLE_OPTIMIZED"
            )

            print(
                "Composite-index measurements were "
                "too variable for a safe conclusion."
            )

            drop_index(
                connection,
                index_name
            )

            print(
                "Composite index removed."
            )

            save_history(
                connection,
                metric_id,
                table_name,
                (
                    f"{filter_column},"
                    f"{order_column}"
                ),
                baseline["median_ms"],
                optimized["median_ms"],
                None,
                decision
            )

            return {
                "decision": decision,
                "index_name": index_name,
                "baseline_time_ms":
                    baseline["median_ms"],
                "optimized_time_ms":
                    optimized["median_ms"],
                "improvement_percent": None
            }

        # =========================================
        # CALCULATE IMPROVEMENT
        # =========================================

        baseline_time = baseline["median_ms"]
        optimized_time = optimized["median_ms"]

        improvement = calculate_improvement(
            baseline_time,
            optimized_time
        )

        print(
            "\n===== COMPOSITE INDEX RESULT ====="
        )

        print(
            f"Baseline median: "
            f"{baseline_time:.3f} ms"
        )

        print(
            f"Optimized median: "
            f"{optimized_time:.3f} ms"
        )

        print(
            f"Observed improvement: "
            f"{improvement:.2f}%"
        )

        # =========================================
        # KEEP / ROLLBACK
        # =========================================

        if improvement >= IMPROVEMENT_THRESHOLD:

            decision = "KEEP INDEX"

            print(
                "\nDecision: KEEP INDEX"
            )

            print(
                f"Stable improvement meets the "
                f"{IMPROVEMENT_THRESHOLD:.1f}% threshold."
            )

        else:

            decision = "ROLLBACK"

            print(
                "\nDecision: ROLLBACK"
            )

            print(
                f"Improvement is below the "
                f"{IMPROVEMENT_THRESHOLD:.1f}% threshold."
            )

            drop_index(
                connection,
                index_name
            )

            print(
                "Composite index removed."
            )

        save_history(
            connection,
            metric_id,
            table_name,
            (
                f"{filter_column},"
                f"{order_column}"
            ),
            baseline_time,
            optimized_time,
            improvement,
            decision
        )

        print(
            "\nOptimization result saved "
            "to history."
        )

        return {
            "decision": decision,
            "index_name": index_name,
            "baseline_time_ms": baseline_time,
            "optimized_time_ms": optimized_time,
            "improvement_percent": improvement
        }

    except Exception:

        connection.rollback()

        # -----------------------------------------
        # Safety recovery
        # -----------------------------------------

        try:

            if index_exists(
                connection,
                index_name
            ):

                print(
                    "\nSafety check: "
                    "candidate index currently exists."
                )

        except Exception:

            connection.rollback()

        raise

    finally:

        connection.close()


if __name__ == "__main__":

    TEST_QUERY = """
        SELECT
            o.order_id,
            o.order_date,
            o.status,
            o.total_amount
        FROM orders o
        WHERE o.customer_id = 5000
        ORDER BY o.order_date DESC;
    """

    result = optimize_composite_index(
        metric_id=3,
        query_text=TEST_QUERY,
        table_name="orders",
        filter_column="customer_id",
        order_column="order_date",
        direction="DESC"
    )

    print(
        "\n===== FINAL RESULT ====="
    )

    print(result)