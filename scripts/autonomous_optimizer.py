import re
import time
import psycopg2


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "cloud_optimizer",
    "user": "postgres",
    "password": "123456t"
}


IMPROVEMENT_THRESHOLD = 5.0
MEASUREMENT_RUNS = 7
MAX_VARIATION_PERCENT = 25.0


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def validate_identifier(identifier):
    if not identifier:
        return False

    return bool(
        re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_]*",
            identifier
        )
    )


def extract_query_condition(query_text):
    if not query_text:
        return None, None, None

    match = re.search(
        r"\bWHERE\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"
        r"(['\"]?)([A-Za-z0-9_.-]+)\2",
        query_text,
        re.IGNORECASE
    )

    if not match:
        return None, None, None

    column_name = match.group(1)
    value = match.group(3)
    quote = match.group(2)

    return column_name, value, quote


def build_index_name(table_name, column_name):
    return f"idx_{table_name}_{column_name}"


def index_exists(connection, index_name):
    query = """
        SELECT EXISTS (
            SELECT 1
            FROM pg_indexes
            WHERE indexname = %s
        );
    """

    cursor = connection.cursor()

    try:
        cursor.execute(
            query,
            (index_name,)
        )

        exists = cursor.fetchone()[0]

        return exists

    finally:
        cursor.close()


def create_index(
    connection,
    table_name,
    column_name
):
    if not validate_identifier(table_name):
        raise ValueError(
            f"Unsafe table name: {table_name}"
        )

    if not validate_identifier(column_name):
        raise ValueError(
            f"Unsafe column name: {column_name}"
        )

    index_name = build_index_name(
        table_name,
        column_name
    )

    existed_before = index_exists(
        connection,
        index_name
    )

    if existed_before:
        print(
            f"Index already exists: {index_name}"
        )

        print(
            "Existing index will be preserved."
        )

        return index_name, False

    query = f"""
        CREATE INDEX {index_name}
        ON {table_name} ({column_name});
    """

    cursor = connection.cursor()

    try:
        cursor.execute(query)
        connection.commit()

    finally:
        cursor.close()

    print(
        f"New index created: {index_name}"
    )

    return index_name, True


def drop_index(
    connection,
    index_name
):
    if not validate_identifier(index_name):
        raise ValueError(
            f"Unsafe index name: {index_name}"
        )

    query = f"""
        DROP INDEX IF EXISTS {index_name};
    """

    cursor = connection.cursor()

    try:
        cursor.execute(query)
        connection.commit()

    finally:
        cursor.close()

    print(
        f"Index removed: {index_name}"
    )


def execute_query(
    connection,
    query_text
):
    cursor = connection.cursor()

    try:
        start_time = time.perf_counter()

        cursor.execute(query_text)
        cursor.fetchall()

        end_time = time.perf_counter()

        execution_time_ms = (
            end_time - start_time
        ) * 1000

        return execution_time_ms

    finally:
        cursor.close()


def measure_query(
    connection,
    query_text,
    runs=MEASUREMENT_RUNS
):
    timings = []

    for _ in range(runs):
        execution_time = execute_query(
            connection,
            query_text
        )

        timings.append(
            execution_time
        )

    timings.sort()

    middle = len(timings) // 2

    if len(timings) % 2 == 0:
        median_time = (
            timings[middle - 1]
            + timings[middle]
        ) / 2
    else:
        median_time = timings[middle]

    minimum_time = min(timings)
    maximum_time = max(timings)

    if median_time > 0:
        variation_percent = (
            (maximum_time - minimum_time)
            / median_time
        ) * 100
    else:
        variation_percent = 0.0

    return {
        "timings": timings,
        "median": median_time,
        "minimum": minimum_time,
        "maximum": maximum_time,
        "variation_percent":
            variation_percent
    }


def calculate_improvement(
    baseline,
    optimized
):
    if baseline <= 0:
        return 0.0

    improvement = (
        (baseline - optimized)
        / baseline
    ) * 100

    return improvement


def is_measurement_stable(
    measurement
):
    return (
        measurement["variation_percent"]
        <= MAX_VARIATION_PERCENT
    )


def print_measurement(
    label,
    measurement
):
    print(
        f"\n{label}"
    )

    print(
        "Individual timings: "
        + ", ".join(
            f"{value:.3f} ms"
            for value in measurement["timings"]
        )
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
        f"Variation: "
        f"{measurement['variation_percent']:.2f}%"
    )

    print(
        f"Measurement stability: "
        f"{'STABLE' if is_measurement_stable(measurement) else 'UNSTABLE'}"
    )


def save_history(
    connection,
    metric_id,
    optimization_type,
    table_name,
    column_name,
    baseline_time,
    optimized_time,
    improvement,
    decision
):
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

    cursor = connection.cursor()

    try:
        cursor.execute(
            query,
            (
                metric_id,
                optimization_type,
                table_name,
                column_name,
                baseline_time,
                optimized_time,
                improvement,
                decision
            )
        )

        connection.commit()

    finally:
        cursor.close()

    print(
        "Optimization result saved to history."
    )


def verify_rollback(
    connection,
    index_name
):
    exists = index_exists(
        connection,
        index_name
    )

    if exists:

        print(
            "ROLLBACK VERIFICATION FAILED: "
            f"{index_name} still exists."
        )

        return False

    print(
        "ROLLBACK VERIFIED: "
        f"{index_name} has been removed."
    )

    return True


def optimize_query(
    metric_id,
    query_text,
    table_name,
    column_name
):
    print(
        "\n===== AUTONOMOUS OPTIMIZATION =====\n"
    )

    print(
        f"Metric ID: {metric_id}"
    )

    print(
        f"Target table: {table_name}"
    )

    print(
        f"Target column: {column_name}"
    )

    print(
        f"Query: {query_text}"
    )

    print(
        f"\nMeasurement runs per phase: "
        f"{MEASUREMENT_RUNS}"
    )

    print(
        f"Maximum allowed timing variation: "
        f"{MAX_VARIATION_PERCENT:.1f}%"
    )

    # SAFETY VALIDATION

    if not validate_identifier(table_name):

        print(
            "\nOptimization cancelled."
        )

        print(
            f"Unsafe table identifier: "
            f"{table_name}"
        )

        return {
            "metric_id": metric_id,
            "table": table_name,
            "column": column_name,
            "baseline_time_ms": None,
            "optimized_time_ms": None,
            "improvement_percent": 0.0,
            "decision": "SAFETY_BLOCK"
        }

    if not validate_identifier(column_name):

        print(
            "\nOptimization cancelled."
        )

        print(
            f"Unsafe column identifier: "
            f"{column_name}"
        )

        return {
            "metric_id": metric_id,
            "table": table_name,
            "column": column_name,
            "baseline_time_ms": None,
            "optimized_time_ms": None,
            "improvement_percent": 0.0,
            "decision": "SAFETY_BLOCK"
        }

    connection = get_connection()

    try:

        # BASELINE MEASUREMENT

        print(
            "\n===== BASELINE MEASUREMENT ====="
        )

        baseline_measurement = measure_query(
            connection,
            query_text
        )

        print_measurement(
            "Baseline performance:",
            baseline_measurement
        )

        baseline_time = (
            baseline_measurement["median"]
        )

        # INDEX CREATION / DETECTION

        index_name, created_by_optimizer = (
            create_index(
                connection,
                table_name,
                column_name
            )
        )

        # EXISTING INDEX PATH

        if not created_by_optimizer:

            print(
                "\nCandidate index already existed."
            )

            print(
                "The system will not recreate "
                "or remove the existing index."
            )

            # CURRENT INDEXED MEASUREMENT

            print(
                "\n===== INDEXED MEASUREMENT ====="
            )

            optimized_measurement = (
                measure_query(
                    connection,
                    query_text
                )
            )

            print_measurement(
                "Indexed performance:",
                optimized_measurement
            )

            optimized_time = (
                optimized_measurement["median"]
            )

            improvement = calculate_improvement(
                baseline_time,
                optimized_time
            )

            baseline_stable = (
                is_measurement_stable(
                    baseline_measurement
                )
            )

            optimized_stable = (
                is_measurement_stable(
                    optimized_measurement
                )
            )

            print(
                f"\nObserved median improvement: "
                f"{improvement:.2f}%"
            )

            print(
                f"Baseline stable: "
                f"{'YES' if baseline_stable else 'NO'}"
            )

            print(
                f"Indexed measurement stable: "
                f"{'YES' if optimized_stable else 'NO'}"
            )

            # EXISTING INDEXES ARE NEVER REMOVED

            if (
                baseline_stable
                and optimized_stable
                and improvement
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
                    f"Index {index_name} "
                    "provides sufficient "
                    "stable improvement."
                )

                print(
                    "Existing index preserved."
                )

            elif (
                baseline_stable
                and optimized_stable
            ):

                decision = (
                    "EXISTING INDEX NOT VERIFIED"
                )

                print(
                    "\nDecision: "
                    "EXISTING INDEX NOT VERIFIED"
                )

                print(
                    "The measurements were stable, "
                    "but the index did not demonstrate "
                    "sufficient improvement."
                )

                print(
                    "Existing index will still "
                    "be preserved."
                )

                print(
                    "No destructive action will "
                    "be performed."
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
                    "Performance measurements "
                    "were too variable for a "
                    "confident optimization conclusion."
                )

                print(
                    "Existing index will be preserved."
                )

                print(
                    "No destructive action will "
                    "be performed."
                )

            save_history(
                connection,
                metric_id,
                "INDEX_OPTIMIZATION",
                table_name,
                column_name,
                baseline_time,
                optimized_time,
                improvement,
                decision
            )

            return {
                "metric_id": metric_id,
                "table": table_name,
                "column": column_name,
                "baseline_time_ms":
                    baseline_time,
                "optimized_time_ms":
                    optimized_time,
                "improvement_percent":
                    improvement,
                "decision": decision
            }

        # NEW INDEX PATH

        time.sleep(0.5)

        print(
            "\n===== OPTIMIZED MEASUREMENT ====="
        )

        optimized_measurement = measure_query(
            connection,
            query_text
        )

        print_measurement(
            "Optimized performance:",
            optimized_measurement
        )

        optimized_time = (
            optimized_measurement["median"]
        )

        # PERFORMANCE COMPARISON

        improvement = calculate_improvement(
            baseline_time,
            optimized_time
        )

        baseline_stable = (
            is_measurement_stable(
                baseline_measurement
            )
        )

        optimized_stable = (
            is_measurement_stable(
                optimized_measurement
            )
        )

        print(
            f"\nMedian performance improvement: "
            f"{improvement:.2f}%"
        )

        # AUTONOMOUS DECISION

        if not baseline_stable:

            decision = (
                "ROLLBACK_UNSTABLE_BASELINE"
            )

            print(
                "\nDecision: "
                "ROLLBACK_UNSTABLE_BASELINE"
            )

            print(
                "Baseline measurements were "
                "too variable."
            )

        elif not optimized_stable:

            decision = (
                "ROLLBACK_UNSTABLE_OPTIMIZED"
            )

            print(
                "\nDecision: "
                "ROLLBACK_UNSTABLE_OPTIMIZED"
            )

            print(
                "Optimized measurements were "
                "too variable."
            )

        elif improvement >= IMPROVEMENT_THRESHOLD:

            decision = "KEEP INDEX"

            print(
                "\nDecision: KEEP INDEX"
            )

            print(
                f"Index {index_name} "
                "provides sufficient stable "
                "improvement."
            )

            print(
                "Optimization committed."
            )

        else:

            decision = "ROLLBACK"

            print(
                "\nDecision: ROLLBACK"
            )

            print(
                f"Index {index_name} "
                "did not provide sufficient "
                "stable improvement."
            )

        # ROLLBACK WHEN REQUIRED

        if decision != "KEEP INDEX":

            print(
                "\nRolling back candidate index..."
            )

            drop_index(
                connection,
                index_name
            )

            rollback_success = (
                verify_rollback(
                    connection,
                    index_name
                )
            )

            if rollback_success:

                print(
                    "Rollback completed successfully."
                )

            else:

                print(
                    "WARNING: Rollback could not "
                    "be fully verified."
                )

        # SAVE HISTORY

        save_history(
            connection,
            metric_id,
            "INDEX_OPTIMIZATION",
            table_name,
            column_name,
            baseline_time,
            optimized_time,
            improvement,
            decision
        )

        return {
            "metric_id": metric_id,
            "table": table_name,
            "column": column_name,
            "baseline_time_ms":
                baseline_time,
            "optimized_time_ms":
                optimized_time,
            "improvement_percent":
                improvement,
            "decision": decision
        }

    except Exception as error:

        print(
            "\n===== OPTIMIZATION ERROR ====="
        )

        print(
            f"Error: {error}"
        )

        print(
            "Optimization failed safely."
        )

        return {
            "metric_id": metric_id,
            "table": table_name,
            "column": column_name,
            "baseline_time_ms": None,
            "optimized_time_ms": None,
            "improvement_percent": 0.0,
            "decision": "ERROR"
        }

    finally:

        connection.close()


def main():

    print(
        "Autonomous optimizer module loaded."
    )

    print(
        "This module expects a decision "
        "from decision_engine.py."
    )


if __name__ == "__main__":
    main()