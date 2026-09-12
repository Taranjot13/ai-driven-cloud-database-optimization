import re
import time
import psycopg2
import statistics


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "cloud_optimizer",
    "user": "postgres",
    "password": "123456t"
}


IMPROVEMENT_THRESHOLD = 5.0

# Number of warm-up executions before measurement.
WARMUP_RUNS = 3

# Number of measurement samples.
MEASUREMENT_RUNS = 7

# Number of query executions inside each measurement sample.
EXECUTIONS_PER_SAMPLE = 10

# Maximum allowed robust variation.
MAX_MAD_VARIATION_PERCENT = 25.0

# Outlier detection threshold.
OUTLIER_MAD_MULTIPLIER = 3.0

# Very small timings are difficult to compare reliably.
MIN_PRACTICAL_TIMING_MS = 0.20


def validate_identifier(identifier):
    """
    Allow only safe PostgreSQL identifiers.
    """
    return bool(
        re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_]*",
            identifier
        )
    )


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def index_exists(connection, index_name):
    """
    Check whether an index already exists.
    """
    query = """
        SELECT EXISTS (
            SELECT 1
            FROM pg_indexes
            WHERE indexname = %s
        );
    """

    with connection.cursor() as cursor:
        cursor.execute(query, (index_name,))
        return cursor.fetchone()[0]


def create_index(
    connection,
    index_name,
    table_name,
    column_name
):
    """
    Create an index using validated identifiers.
    """
    if not (
        validate_identifier(index_name)
        and validate_identifier(table_name)
        and validate_identifier(column_name)
    ):
        raise ValueError(
            "Invalid database identifier."
        )

    query = (
        f"CREATE INDEX {index_name} "
        f"ON {table_name} ({column_name});"
    )

    with connection.cursor() as cursor:
        cursor.execute(query)

    connection.commit()


def drop_index(connection, index_name):
    """
    Drop an index using a validated identifier.
    """
    if not validate_identifier(index_name):
        raise ValueError(
            "Invalid index identifier."
        )

    query = (
        f"DROP INDEX IF EXISTS {index_name};"
    )

    with connection.cursor() as cursor:
        cursor.execute(query)

    connection.commit()


def execute_query(connection, query_text):
    """
    Execute a read-only query and measure execution time.
    """
    with connection.cursor() as cursor:
        start_time = time.perf_counter()

        cursor.execute(query_text)

        if cursor.description is not None:
            cursor.fetchall()

        end_time = time.perf_counter()

        return (
            end_time - start_time
        ) * 1000


def validate_query(query_text):
    """
    Ensure that the optimizer only evaluates
    read-oriented SQL statements.

    This protects the optimizer from accidentally
    executing INSERT, UPDATE, DELETE, DROP, etc.
    """
    normalized_query = (
        query_text.strip()
        .lower()
    )

    allowed_prefixes = (
        "select",
        "with"
    )

    if not normalized_query.startswith(
        allowed_prefixes
    ):
        raise ValueError(
            "Autonomous optimizer only supports "
            "SELECT/WITH queries."
        )


def warm_up_query(
    connection,
    query_text
):
    """
    Execute the query several times before measurement.

    This allows PostgreSQL and the operating system
    to warm relevant caches.
    """
    print(
        f"\nRunning {WARMUP_RUNS} "
        "warm-up executions..."
    )

    for _ in range(WARMUP_RUNS):
        execute_query(
            connection,
            query_text
        )

    print(
        "Warm-up completed."
    )


def calculate_mad(values):
    """
    Calculate Median Absolute Deviation.
    """
    median_value = statistics.median(
        values
    )

    absolute_deviations = [
        abs(value - median_value)
        for value in values
    ]

    return statistics.median(
        absolute_deviations
    )


def calculate_robust_variation_percent(
    values
):
    """
    Calculate MAD-based robust variation.

    A minimum practical timing floor is used
    for extremely small execution times so that
    tiny absolute timing noise does not dominate
    the percentage calculation.
    """
    median_value = statistics.median(
        values
    )

    mad_value = calculate_mad(
        values
    )

    denominator = max(
        median_value,
        MIN_PRACTICAL_TIMING_MS
    )

    if denominator == 0:
        return 0.0

    return (
        mad_value / denominator
    ) * 100


def identify_outliers(values):
    """
    Identify extreme timing outliers using MAD.
    """
    median_value = statistics.median(
        values
    )

    mad_value = calculate_mad(
        values
    )

    if mad_value == 0:
        return []

    threshold = (
        mad_value
        * OUTLIER_MAD_MULTIPLIER
    )

    outliers = [
        value
        for value in values
        if abs(
            value - median_value
        ) > threshold
    ]

    return outliers


def measure_query(
    connection,
    query_text
):
    """
    Warm up the query and then perform
    multiple repeated measurement samples.

    Each sample executes the query multiple
    times and records the average time.

    The final decision uses the median
    and MAD of those samples.
    """

    warm_up_query(
        connection,
        query_text
    )

    sample_timings = []

    print(
        f"\nCollecting "
        f"{MEASUREMENT_RUNS} measurement samples..."
    )

    print(
        f"Each sample executes the query "
        f"{EXECUTIONS_PER_SAMPLE} times."
    )

    for sample_number in range(
        MEASUREMENT_RUNS
    ):
        timings = []

        for _ in range(
            EXECUTIONS_PER_SAMPLE
        ):
            execution_time = execute_query(
                connection,
                query_text
            )

            timings.append(
                execution_time
            )

        sample_average = (
            statistics.mean(timings)
        )

        sample_timings.append(
            sample_average
        )

        print(
            f"Sample "
            f"{sample_number + 1}: "
            f"{sample_average:.3f} ms"
        )

    median_value = statistics.median(
        sample_timings
    )

    minimum_value = min(
        sample_timings
    )

    maximum_value = max(
        sample_timings
    )

    mad_value = calculate_mad(
        sample_timings
    )

    robust_variation = (
        calculate_robust_variation_percent(
            sample_timings
        )
    )

    outliers = identify_outliers(
        sample_timings
    )

    return {
        "timings": sample_timings,
        "median": median_value,
        "minimum": minimum_value,
        "maximum": maximum_value,
        "mad": mad_value,
        "robust_variation": robust_variation,
        "outliers": outliers
    }


def is_measurement_stable(
    measurement
):
    """
    Determine whether the measurement
    is sufficiently stable.
    """

    robust_stability = (
        measurement[
            "robust_variation"
        ]
        <= MAX_MAD_VARIATION_PERCENT
    )

    return robust_stability


def print_measurement(
    title,
    measurement
):
    """
    Print detailed measurement statistics.
    """

    print(
        f"\n===== {title} ====="
    )

    timing_text = ", ".join(
        f"{value:.3f} ms"
        for value in measurement[
            "timings"
        ]
    )

    print(
        f"Measurement samples: "
        f"{timing_text}"
    )

    print(
        f"Median: "
        f"{measurement['median']:.3f} ms"
    )

    print(
        f"Minimum: "
        f"{measurement['minimum']:.3f} ms"
    )

    print(
        f"Maximum: "
        f"{measurement['maximum']:.3f} ms"
    )

    print(
        f"MAD: "
        f"{measurement['mad']:.3f} ms"
    )

    print(
        f"Robust variation: "
        f"{measurement['robust_variation']:.2f}%"
    )

    if measurement["outliers"]:
        outlier_text = ", ".join(
            f"{value:.3f} ms"
            for value in measurement[
                "outliers"
            ]
        )

        print(
            f"Detected timing outliers: "
            f"{outlier_text}"
        )

    else:
        print(
            "Detected timing outliers: None"
        )

    stable = is_measurement_stable(
        measurement
    )

    print(
        "Measurement stability: "
        f"{'STABLE' if stable else 'UNSTABLE'}"
    )

    if measurement["median"] < MIN_PRACTICAL_TIMING_MS:
        print(
            "Measurement note: "
            "Execution time is below the "
            "practical timing threshold."
        )


def save_optimization_history(
    connection,
    metric_id,
    optimization_type,
    table_name,
    column_name,
    baseline_time_ms,
    optimized_time_ms,
    improvement_percent,
    decision
):
    """
    Save optimization result to history.
    """

    query = """
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
    """

    with connection.cursor() as cursor:
        cursor.execute(
            query,
            (
                metric_id,
                optimization_type,
                table_name,
                column_name,
                baseline_time_ms,
                optimized_time_ms,
                improvement_percent,
                decision
            )
        )

    connection.commit()


def calculate_improvement(
    baseline_time,
    optimized_time
):
    """
    Calculate percentage performance improvement.
    """

    if baseline_time <= 0:
        return 0.0

    return (
        (
            baseline_time
            - optimized_time
        )
        / baseline_time
    ) * 100


def optimize_query(
    metric_id,
    query_text,
    table_name,
    column_name
):
    """
    Safely evaluate an index optimization.

    Pipeline:

    Monitor
        ↓
    Warm-up
        ↓
    Baseline measurement
        ↓
    Existing-index detection
        ↓
    Indexed measurement
        ↓
    Robust statistical verification
        ↓
    Keep / Rollback / Verify
        ↓
    Save history
    """

    connection = None

    try:
        validate_query(
            query_text
        )

        connection = get_connection()

        index_name = (
            f"idx_{table_name}_{column_name}"
        )

        if not (
            validate_identifier(
                table_name
            )
            and validate_identifier(
                column_name
            )
        ):
            raise ValueError(
                "Invalid table or column identifier."
            )

        print(
            "\n===== AUTONOMOUS OPTIMIZATION ====="
        )

        print(
            f"Target: "
            f"{table_name}.{column_name}"
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
            f"Minimum practical timing: "
            f"{MIN_PRACTICAL_TIMING_MS:.2f} ms"
        )

        # =========================================
        # BASELINE
        # =========================================

        baseline = measure_query(
            connection,
            query_text
        )

        print_measurement(
            "BASELINE MEASUREMENT",
            baseline
        )

        baseline_stable = (
            is_measurement_stable(
                baseline
            )
        )

        # =========================================
        # CHECK EXISTING INDEX
        # =========================================

        existing_index = index_exists(
            connection,
            index_name
        )

        if existing_index:

            print(
                f"\nIndex already exists: "
                f"{index_name}"
            )

            print(
                "Existing index will be preserved."
            )

            indexed = measure_query(
                connection,
                query_text
            )

            print_measurement(
                "INDEXED MEASUREMENT",
                indexed
            )

            indexed_stable = (
                is_measurement_stable(
                    indexed
                )
            )

            baseline_median = (
                baseline["median"]
            )

            indexed_median = (
                indexed["median"]
            )

            improvement_percent = (
                calculate_improvement(
                    baseline_median,
                    indexed_median
                )
            )

            print(
                f"\nObserved median improvement: "
                f"{improvement_percent:.2f}%"
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
            ):

                if (
                    improvement_percent
                    >= IMPROVEMENT_THRESHOLD
                ):

                    decision = (
                        "EXISTING INDEX VERIFIED"
                    )

                    print(
                        "\nDecision: "
                        "EXISTING INDEX VERIFIED"
                    )

                    print(
                        "The existing index shows "
                        "a stable performance benefit."
                    )

                else:

                    decision = (
                        "EXISTING INDEX NOT VERIFIED"
                    )

                    print(
                        "\nDecision: "
                        "EXISTING INDEX NOT VERIFIED"
                    )

                    print(
                        "The existing index did not "
                        "show enough stable improvement."
                    )

            else:

                decision = (
                    "MEASUREMENT UNSTABLE"
                )

                print(
                    "\nDecision: "
                    "MEASUREMENT UNSTABLE"
                )

                print(
                    "Measurements were too variable "
                    "for a confident optimization conclusion."
                )

            save_optimization_history(
                connection=connection,
                metric_id=metric_id,
                optimization_type=(
                    "INDEX_VERIFICATION"
                ),
                table_name=table_name,
                column_name=column_name,
                baseline_time_ms=(
                    baseline_median
                ),
                optimized_time_ms=(
                    indexed_median
                ),
                improvement_percent=(
                    improvement_percent
                ),
                decision=decision
            )

            print(
                "\nExisting index preserved."
            )

            print(
                "Optimization result saved "
                "to history."
            )

            return {
                "baseline_time_ms": (
                    baseline_median
                ),
                "optimized_time_ms": (
                    indexed_median
                ),
                "improvement_percent": (
                    improvement_percent
                ),
                "decision": decision
            }

        # =========================================
        # NEW INDEX EXPERIMENT
        # =========================================

        print(
            f"\nIndex does not exist: "
            f"{index_name}"
        )

        if not baseline_stable:

            decision = (
                "ROLLBACK_UNSTABLE_BASELINE"
            )

            print(
                "\nDecision: "
                "ROLLBACK_UNSTABLE_BASELINE"
            )

            print(
                "Baseline measurement is too unstable."
            )

            print(
                "No index will be created."
            )

            save_optimization_history(
                connection=connection,
                metric_id=metric_id,
                optimization_type=(
                    "INDEX_OPTIMIZATION"
                ),
                table_name=table_name,
                column_name=column_name,
                baseline_time_ms=(
                    baseline["median"]
                ),
                optimized_time_ms=(
                    baseline["median"]
                ),
                improvement_percent=0.0,
                decision=decision
            )

            return {
                "baseline_time_ms": (
                    baseline["median"]
                ),
                "optimized_time_ms": (
                    baseline["median"]
                ),
                "improvement_percent": 0.0,
                "decision": decision
            }

        # =========================================
        # CREATE INDEX
        # =========================================

        print(
            f"\nCreating index: "
            f"{index_name}"
        )

        create_index(
            connection,
            index_name,
            table_name,
            column_name
        )

        print(
            "Index created successfully."
        )

        # =========================================
        # INDEXED MEASUREMENT
        # =========================================

        indexed = measure_query(
            connection,
            query_text
        )

        print_measurement(
            "INDEXED MEASUREMENT",
            indexed
        )

        indexed_stable = (
            is_measurement_stable(
                indexed
            )
        )

        baseline_median = (
            baseline["median"]
        )

        indexed_median = (
            indexed["median"]
        )

        improvement_percent = (
            calculate_improvement(
                baseline_median,
                indexed_median
            )
        )

        print(
            f"\nObserved median improvement: "
            f"{improvement_percent:.2f}%"
        )

        print(
            "Baseline stable: "
            f"{'YES' if baseline_stable else 'NO'}"
        )

        print(
            "Indexed measurement stable: "
            f"{'YES' if indexed_stable else 'NO'}"
        )

        # =========================================
        # SAFETY DECISION
        # =========================================

        if not indexed_stable:

            decision = (
                "ROLLBACK_UNSTABLE_OPTIMIZED"
            )

            print(
                "\nDecision: "
                "ROLLBACK_UNSTABLE_OPTIMIZED"
            )

            print(
                "Optimized measurement is unstable."
            )

            print(
                "Rolling back newly created index."
            )

            drop_index(
                connection,
                index_name
            )

            print(
                "Index removed successfully."
            )

        elif (
            improvement_percent
            >= IMPROVEMENT_THRESHOLD
        ):

            decision = "KEEP INDEX"

            print(
                "\nDecision: KEEP INDEX"
            )

            print(
                "Stable improvement exceeds "
                f"{IMPROVEMENT_THRESHOLD:.1f}%."
            )

        else:

            decision = "ROLLBACK"

            print(
                "\nDecision: ROLLBACK"
            )

            print(
                "Performance improvement is below "
                f"{IMPROVEMENT_THRESHOLD:.1f}%."
            )

            drop_index(
                connection,
                index_name
            )

            print(
                "Index removed successfully."
            )

        # =========================================
        # SAVE RESULT
        # =========================================

        save_optimization_history(
            connection=connection,
            metric_id=metric_id,
            optimization_type=(
                "INDEX_OPTIMIZATION"
            ),
            table_name=table_name,
            column_name=column_name,
            baseline_time_ms=(
                baseline_median
            ),
            optimized_time_ms=(
                indexed_median
            ),
            improvement_percent=(
                improvement_percent
            ),
            decision=decision
        )

        print(
            "\nOptimization result saved "
            "to history."
        )

        return {
            "baseline_time_ms": (
                baseline_median
            ),
            "optimized_time_ms": (
                indexed_median
            ),
            "improvement_percent": (
                improvement_percent
            ),
            "decision": decision
        }

    except Exception as error:

        if connection is not None:
            connection.rollback()

        print(
            f"\nOptimization error: "
            f"{error}"
        )

        raise

    finally:

        if connection is not None:
            connection.close()

def optimize_index(
    metric_id,
    query_text,
    table_name,
    column_name
):
    """
    Compatibility wrapper used by the autonomous
    decision pipeline.

    The decision engine calls optimize_index(),
    while the core optimizer is implemented
    by optimize_query().
    """

    return optimize_query(
        metric_id=metric_id,
        query_text=query_text,
        table_name=table_name,
        column_name=column_name
    )