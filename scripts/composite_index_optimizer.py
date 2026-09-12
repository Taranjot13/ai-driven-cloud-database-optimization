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


def get_connection():
    return psycopg2.connect(
        **DB_CONFIG
    )


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
    representative value for EXPLAIN ANALYZE.
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
    Execute the query and consume all rows.
    """

    cursor = connection.cursor()

    start_query = """
        SELECT clock_timestamp();
    """

    cursor.execute(
        start_query
    )

    start_time = cursor.fetchone()[0]

    cursor.execute(
        query
    )

    cursor.fetchall()

    cursor.execute(
        """
        SELECT clock_timestamp();
        """
    )

    end_time = cursor.fetchone()[0]

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

        sample_average = (
            statistics.mean(
                executions
            )
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

    exists = cursor.fetchone()[0]

    cursor.close()

    return exists


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

    if direction.upper() not in {
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
            {order_column} {direction.upper()}
        );
    """

    cursor = connection.cursor()

    cursor.execute(
        sql
    )

    connection.commit()

    cursor.close()


def drop_index(
    connection,
    index_name
):
    validate_identifier(
        index_name
    )

    cursor = connection.cursor()

    cursor.execute(
        f"""
        DROP INDEX IF EXISTS {index_name};
        """
    )

    connection.commit()

    cursor.close()


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

    cursor.close()


def optimize_composite_index(
    metric_id,
    query_text,
    table_name,
    filter_column,
    order_column,
    direction="DESC"
):
    """
    Safely test a composite index.

    The index is kept only when both measurements
    are stable and the observed improvement is positive.
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

    normalized_query = (
        normalize_query(
            query_text
        )
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
            f"{order_column} {direction}"
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
            f"{MAX_MAD_VARIATION_PERCENT}%"
        )

        # -------------------------------------------------
        # Safety check.
        # -------------------------------------------------

        if index_exists(
            connection,
            index_name
        ):

            print(
                "\nComposite index already exists:"
            )

            print(
                index_name
            )

            print(
                "Existing index will not be "
                "recreated."
            )

            return {
                "decision":
                    "EXISTING_INDEX",
                "index_name":
                    index_name
            }

        # -------------------------------------------------
        # Baseline measurement.
        # -------------------------------------------------

        baseline = measure_query(
            connection,
            normalized_query,
            "baseline"
        )

        # -------------------------------------------------
        # Baseline stability protection.
        # -------------------------------------------------

        if not baseline["stable"]:

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
                "ROLLBACK_UNSTABLE_BASELINE"
            )

            return {
                "decision":
                    "ROLLBACK_UNSTABLE_BASELINE",
                "index_name":
                    index_name,
                "baseline_time_ms":
                    baseline["median_ms"],
                "optimized_time_ms":
                    None,
                "improvement_percent":
                    None
            }

        # -------------------------------------------------
        # Create candidate index.
        # -------------------------------------------------

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
            f"Created: "
            f"{index_name}"
        )

        # -------------------------------------------------
        # Optimized measurement.
        # -------------------------------------------------

        optimized = measure_query(
            connection,
            normalized_query,
            "composite indexed"
        )

        # -------------------------------------------------
        # Optimized stability protection.
        # -------------------------------------------------

        if not optimized["stable"]:

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
                "ROLLBACK_UNSTABLE_OPTIMIZED"
            )

            return {
                "decision":
                    "ROLLBACK_UNSTABLE_OPTIMIZED",
                "index_name":
                    index_name,
                "baseline_time_ms":
                    baseline["median_ms"],
                "optimized_time_ms":
                    optimized["median_ms"],
                "improvement_percent":
                    None
            }

        # -------------------------------------------------
        # Calculate improvement.
        # -------------------------------------------------

        baseline_time = (
            baseline["median_ms"]
        )

        optimized_time = (
            optimized["median_ms"]
        )

        if baseline_time <= 0:

            improvement = 0.0

        else:

            improvement = (
                (
                    baseline_time
                    - optimized_time
                )
                / baseline_time
            ) * 100

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

        # -------------------------------------------------
        # Keep or rollback.
        # -------------------------------------------------

        if improvement > 0:

            decision = (
                "KEEP INDEX"
            )

            print(
                "\nDecision: KEEP INDEX"
            )

            print(
                "The composite index produced "
                "a stable positive improvement."
            )

        else:

            decision = (
                "ROLLBACK"
            )

            print(
                "\nDecision: ROLLBACK"
            )

            print(
                "The composite index did not "
                "produce a positive improvement."
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
            "decision":
                decision,
            "index_name":
                index_name,
            "baseline_time_ms":
                baseline_time,
            "optimized_time_ms":
                optimized_time,
            "improvement_percent":
                improvement
        }

    except Exception:

        connection.rollback()

        # -------------------------------------------------
        # Safety cleanup.
        # -------------------------------------------------

        try:

            if index_exists(
                connection,
                index_name
            ):

                print(
                    "\nSafety cleanup: "
                    "removing candidate index..."
                )

                drop_index(
                    connection,
                    index_name
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
