import re
import psycopg2


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "cloud_optimizer",
    "user": "postgres",
    "password": "123456t"
}


SLOW_QUERY_THRESHOLD_MS = 5.0


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def validate_query(query):
    cleaned_query = query.strip()

    if not re.match(
        r"^(SELECT|WITH)\b",
        cleaned_query,
        re.IGNORECASE
    ):
        raise ValueError(
            "Only SELECT and WITH queries are allowed."
        )


def normalize_query_for_explain(query):
    normalized_query = query

    normalized_query = re.sub(
        r"%s",
        "5000",
        normalized_query
    )

    normalized_query = re.sub(
        r"\$\d+",
        "5000",
        normalized_query
    )

    return normalized_query


def run_explain_analyze(query):
    validate_query(query)

    normalized_query = (
        normalize_query_for_explain(query)
    )

    explain_query = f"""
        EXPLAIN (
            ANALYZE,
            BUFFERS,
            FORMAT TEXT
        )
        {normalized_query}
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            explain_query
        )

        rows = cursor.fetchall()

        plan = "\n".join(
            row[0]
            for row in rows
        )

        cursor.close()

        return plan

    finally:
        connection.close()


def extract_execution_time(plan):
    match = re.search(
        r"Execution Time:\s*([\d.]+)\s*ms",
        plan,
        re.IGNORECASE
    )

    if match:
        return float(match.group(1))

    return None


def extract_planning_time(plan):
    match = re.search(
        r"Planning Time:\s*([\d.]+)\s*ms",
        plan,
        re.IGNORECASE
    )

    if match:
        return float(match.group(1))

    return None


def detect_sequential_scan(plan):
    return bool(
        re.search(
            r"\bSeq Scan\b",
            plan,
            re.IGNORECASE
        )
    )


def detect_index_scan(plan):
    return bool(
        re.search(
            r"\bIndex Scan\b|\bIndex Only Scan\b",
            plan,
            re.IGNORECASE
        )
    )


def detect_bitmap_scan(plan):
    return bool(
        re.search(
            r"\bBitmap Heap Scan\b|\bBitmap Index Scan\b",
            plan,
            re.IGNORECASE
        )
    )


def detect_sort(plan):
    return bool(
        re.search(
            r"^\s*Sort\s",
            plan,
            re.MULTILINE | re.IGNORECASE
        )
    )


def detect_nested_loop(plan):
    return bool(
        re.search(
            r"\bNested Loop\b",
            plan,
            re.IGNORECASE
        )
    )


def extract_filter_conditions(plan):
    return re.findall(
        r"Filter:\s*(.+)",
        plan
    )


def extract_index_conditions(plan):
    return re.findall(
        r"Index Cond:\s*(.+)",
        plan
    )


def extract_relation_names(plan):
    """
    Extract actual table names only.

    Bitmap Index Scan is intentionally excluded because
    the object following it is an index, not a table.
    """

    relations = []

    patterns = [
        r"\bSeq Scan on\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        r"\bIndex Scan using\s+[a-zA-Z_][a-zA-Z0-9_]*\s+on\s+"
        r"([a-zA-Z_][a-zA-Z0-9_]*)",
        r"\bIndex Only Scan using\s+[a-zA-Z_][a-zA-Z0-9_]*\s+on\s+"
        r"([a-zA-Z_][a-zA-Z0-9_]*)",
        r"\bBitmap Heap Scan on\s+([a-zA-Z_][a-zA-Z0-9_]*)"
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            plan,
            re.IGNORECASE
        )

        for relation in matches:

            if relation not in relations:
                relations.append(
                    relation
                )

    return relations


def extract_index_names(plan):
    indexes = []

    normal_indexes = re.findall(
        r"Index Scan using\s+"
        r"([a-zA-Z_][a-zA-Z0-9_]*)",
        plan,
        re.IGNORECASE
    )

    bitmap_indexes = re.findall(
        r"Bitmap Index Scan on\s+"
        r"([a-zA-Z_][a-zA-Z0-9_]*)",
        plan,
        re.IGNORECASE
    )

    for index_name in (
        normal_indexes + bitmap_indexes
    ):

        if index_name not in indexes:
            indexes.append(
                index_name
            )

    return indexes


def extract_rows_removed(plan):
    matches = re.findall(
        r"Rows Removed by Filter:\s*(\d+)",
        plan
    )

    return [
        int(value)
        for value in matches
    ]


def extract_filter_column(query):
    """
    Extract a simple equality-filter column.

    Example:
        WHERE o.customer_id = 5000

    Returns:
        customer_id
    """

    match = re.search(
        r"\bWHERE\s+(?:[a-zA-Z_][a-zA-Z0-9_]*\.)?"
        r"([a-zA-Z_][a-zA-Z0-9_]*)\s*=",
        query,
        re.IGNORECASE
    )

    if match:
        return match.group(1)

    return None


def extract_order_by_columns(query):
    """
    Extract ORDER BY columns and direction.

    Example:
        ORDER BY o.order_date DESC

    Returns:
        [
            {
                "column": "order_date",
                "direction": "DESC"
            }
        ]
    """

    match = re.search(
        r"\bORDER\s+BY\s+(.+?)(?:\s+LIMIT\b|\s*$)",
        query,
        re.IGNORECASE | re.DOTALL
    )

    if not match:
        return []

    order_expression = match.group(1)

    columns = []

    parts = order_expression.split(",")

    for part in parts:

        part = part.strip()

        column_match = re.match(
            r"(?:[a-zA-Z_][a-zA-Z0-9_]*\.)?"
            r"([a-zA-Z_][a-zA-Z0-9_]*)"
            r"(?:\s+(ASC|DESC))?",
            part,
            re.IGNORECASE
        )

        if column_match:

            column = column_match.group(1)

            direction = (
                column_match.group(2)
                or "ASC"
            ).upper()

            columns.append({
                "column": column,
                "direction": direction
            })

    return columns


def detect_composite_index_candidate(
    query,
    plan
):
    """
    Detect the common pattern:

        WHERE filter_column = value
        ORDER BY sort_column

    If PostgreSQL is filtering with one index and then
    performing a separate Sort, a composite index may
    be worth testing.
    """

    if not detect_sort(plan):
        return None

    filter_column = extract_filter_column(
        query
    )

    order_columns = extract_order_by_columns(
        query
    )

    if not filter_column:
        return None

    if not order_columns:
        return None

    first_order_column = order_columns[0]

    order_column = first_order_column[
        "column"
    ]

    direction = first_order_column[
        "direction"
    ]

    if filter_column == order_column:
        return None

    return {
        "type": "COMPOSITE_INDEX_CANDIDATE",
        "columns": [
            filter_column,
            order_column
        ],
        "index_definition": (
            f"({filter_column}, "
            f"{order_column} {direction})"
        ),
        "reason": (
            f"The query filters on "
            f"{filter_column} and then sorts by "
            f"{order_column} {direction}. "
            "A composite index may support both "
            "operations and should be tested before "
            "being permanently adopted."
        ),
        "confidence": "HIGH"
    }


def identify_optimization_candidates(
    query,
    plan,
    execution_time
):
    candidates = []

    sequential_scan = (
        detect_sequential_scan(plan)
    )

    index_scan = (
        detect_index_scan(plan)
    )

    bitmap_scan = (
        detect_bitmap_scan(plan)
    )

    sort_operation = (
        detect_sort(plan)
    )

    nested_loop = (
        detect_nested_loop(plan)
    )

    rows_removed = (
        extract_rows_removed(plan)
    )

    indexes = (
        extract_index_names(plan)
    )

    if sequential_scan:

        if any(
            value > 0
            for value in rows_removed
        ):

            candidates.append({
                "type": "INDEX_CANDIDATE",
                "reason": (
                    "PostgreSQL is performing a sequential "
                    "scan and filtering rows. An index may "
                    "reduce unnecessary row scanning."
                ),
                "confidence": "HIGH"
            })

        else:

            candidates.append({
                "type": "SEQUENTIAL_SCAN",
                "reason": (
                    "PostgreSQL is using a sequential scan. "
                    "Table size and workload should be "
                    "reviewed before creating an index."
                ),
                "confidence": "MEDIUM"
            })

    if index_scan or bitmap_scan:

        index_name = (
            indexes[0]
            if indexes
            else "existing index"
        )

        candidates.append({
            "type": "INDEX_USAGE",
            "reason": (
                f"PostgreSQL is already using "
                f"{index_name}. Creating another index "
                "for the same access pattern is not "
                "recommended without additional evidence."
            ),
            "confidence": "HIGH"
        })

    composite_candidate = (
        detect_composite_index_candidate(
            query,
            plan
        )
    )

    if composite_candidate:

        candidates.append(
            composite_candidate
        )

    if (
        (index_scan or bitmap_scan)
        and execution_time is not None
        and execution_time > SLOW_QUERY_THRESHOLD_MS
    ):

        candidates.append({
            "type":
                "INDEXED_QUERY_PERFORMANCE_WARNING",
            "reason": (
                "The query is using an index but remains "
                "above the project performance threshold."
            ),
            "confidence": "HIGH"
        })

    if sort_operation:

        candidates.append({
            "type": "SORT_OPTIMIZATION",
            "reason": (
                "A sort operation is present. "
                "Ordering columns and suitable indexes "
                "should be evaluated."
            ),
            "confidence": "MEDIUM"
        })

    if nested_loop:

        candidates.append({
            "type": "JOIN_OPTIMIZATION",
            "reason": (
                "A nested-loop join is present. "
                "Join conditions and indexes should "
                "be reviewed."
            ),
            "confidence": "MEDIUM"
        })

    return candidates


def build_diagnosis(
    query,
    plan,
    execution_time
):
    sequential_scan = (
        detect_sequential_scan(plan)
    )

    index_scan = (
        detect_index_scan(plan)
    )

    bitmap_scan = (
        detect_bitmap_scan(plan)
    )

    composite_candidate = (
        detect_composite_index_candidate(
            query,
            plan
        )
    )

    if composite_candidate:

        return {
            "status":
                "COMPOSITE_INDEX_CANDIDATE",
            "diagnosis": (
                "The query is using an existing index "
                "for filtering but performs a separate "
                "sort operation. A composite index "
                "covering the filter and ordering columns "
                "may improve the access path."
            ),
            "recommended_action":
                "TEST_COMPOSITE_INDEX"
        }

    if (
        (index_scan or bitmap_scan)
        and execution_time is not None
        and execution_time > SLOW_QUERY_THRESHOLD_MS
    ):

        return {
            "status":
                "SLOW_WITH_INDEX",
            "diagnosis": (
                "The query is using an index but execution "
                "time is above the project threshold."
            ),
            "recommended_action":
                "REVIEW_QUERY_AND_RESOURCES"
        }

    if (
        (index_scan or bitmap_scan)
        and execution_time is not None
        and execution_time <= SLOW_QUERY_THRESHOLD_MS
    ):

        return {
            "status":
                "INDEXED_AND_WITHIN_THRESHOLD",
            "diagnosis": (
                "The query is using an index and execution "
                "time is within the project threshold."
            ),
            "recommended_action":
                "MONITOR"
        }

    if sequential_scan:

        return {
            "status":
                "SEQUENTIAL_SCAN",
            "diagnosis": (
                "The query is using a sequential scan. "
                "An index may be beneficial if the "
                "filtered column is selective."
            ),
            "recommended_action":
                "EVALUATE_INDEX"
        }

    if (
        execution_time is not None
        and execution_time > SLOW_QUERY_THRESHOLD_MS
    ):

        return {
            "status":
                "SLOW_QUERY",
            "diagnosis": (
                "The query exceeds the project "
                "performance threshold."
            ),
            "recommended_action":
                "ANALYZE_WORKLOAD"
        }

    return {
        "status":
            "NORMAL",
        "diagnosis": (
            "The query is within the configured "
            "performance threshold."
        ),
        "recommended_action":
            "MONITOR"
    }


def analyze_query_plan(query):

    print(
        "\n===== QUERY PLAN ANALYZER =====\n"
    )

    print(
        "Original query:"
    )

    print(query)

    normalized_query = (
        normalize_query_for_explain(query)
    )

    if normalized_query != query:

        print(
            "\nQuery used for EXPLAIN ANALYZE:"
        )

        print(
            normalized_query
        )

    print(
        "\nRunning EXPLAIN ANALYZE..."
    )

    plan = run_explain_analyze(
        query
    )

    execution_time = (
        extract_execution_time(plan)
    )

    planning_time = (
        extract_planning_time(plan)
    )

    sequential_scan = (
        detect_sequential_scan(plan)
    )

    index_scan = (
        detect_index_scan(plan)
    )

    bitmap_scan = (
        detect_bitmap_scan(plan)
    )

    sort_operation = (
        detect_sort(plan)
    )

    nested_loop = (
        detect_nested_loop(plan)
    )

    relations = (
        extract_relation_names(plan)
    )

    indexes = (
        extract_index_names(plan)
    )

    filter_conditions = (
        extract_filter_conditions(plan)
    )

    index_conditions = (
        extract_index_conditions(plan)
    )

    rows_removed = (
        extract_rows_removed(plan)
    )

    diagnosis = build_diagnosis(
        query,
        plan,
        execution_time
    )

    candidates = (
        identify_optimization_candidates(
            query,
            plan,
            execution_time
        )
    )

    print(
        "\n===== EXECUTION PLAN ====="
    )

    print(plan)

    print(
        "\n===== PLAN ANALYSIS ====="
    )

    if planning_time is not None:
        print(
            f"Planning time: "
            f"{planning_time:.3f} ms"
        )
    else:
        print(
            "Planning time: unavailable"
        )

    if execution_time is not None:
        print(
            f"Execution time: "
            f"{execution_time:.3f} ms"
        )
    else:
        print(
            "Execution time: unavailable"
        )

    print(
        f"Sequential scan: "
        f"{'YES' if sequential_scan else 'NO'}"
    )

    print(
        f"Index scan: "
        f"{'YES' if index_scan else 'NO'}"
    )

    print(
        f"Bitmap scan: "
        f"{'YES' if bitmap_scan else 'NO'}"
    )

    print(
        f"Sort operation: "
        f"{'YES' if sort_operation else 'NO'}"
    )

    print(
        f"Nested Loop: "
        f"{'YES' if nested_loop else 'NO'}"
    )

    print(
        "\nTables detected:"
    )

    if relations:

        for relation in relations:
            print(
                f"- {relation}"
            )

    else:

        print(
            "- None"
        )

    print(
        "\nIndexes detected:"
    )

    if indexes:

        for index in indexes:
            print(
                f"- {index}"
            )

    else:

        print(
            "- None"
        )

    print(
        "\nFilter conditions:"
    )

    if filter_conditions:

        for condition in filter_conditions:
            print(
                f"- {condition}"
            )

    else:

        print(
            "- None"
        )

    print(
        "\nIndex conditions:"
    )

    if index_conditions:

        for condition in index_conditions:
            print(
                f"- {condition}"
            )

    else:

        print(
            "- None"
        )

    print(
        "\nRows removed by filter:"
    )

    if rows_removed:

        for value in rows_removed:
            print(
                f"- {value}"
            )

    else:

        print(
            "- None"
        )

    print(
        "\n===== SYSTEM DIAGNOSIS ====="
    )

    print(
        f"Status: "
        f"{diagnosis['status']}"
    )

    print(
        f"Diagnosis: "
        f"{diagnosis['diagnosis']}"
    )

    print(
        f"Recommended action: "
        f"{diagnosis['recommended_action']}"
    )

    print(
        "\n===== OPTIMIZATION CANDIDATES ====="
    )

    if candidates:

        for index, candidate in enumerate(
            candidates,
            start=1
        ):

            print(
                f"\nCandidate {index}: "
                f"{candidate['type']}"
            )

            print(
                f"Reason: "
                f"{candidate['reason']}"
            )

            print(
                f"Confidence: "
                f"{candidate['confidence']}"
            )

            if "index_definition" in candidate:

                print(
                    f"Suggested index: "
                    f"{candidate['index_definition']}"
                )

    else:

        print(
            "No optimization candidates detected."
        )

    return {
        "query": query,
        "normalized_query": normalized_query,
        "plan": plan,
        "planning_time_ms": planning_time,
        "execution_time_ms": execution_time,
        "sequential_scan": sequential_scan,
        "index_scan": index_scan,
        "bitmap_scan": bitmap_scan,
        "sort_operation": sort_operation,
        "nested_loop": nested_loop,
        "tables": relations,
        "indexes": indexes,
        "filter_conditions": filter_conditions,
        "index_conditions": index_conditions,
        "rows_removed": rows_removed,
        "diagnosis": diagnosis,
        "optimization_candidates": candidates
    }


if __name__ == "__main__":

    TEST_QUERY = """
        SELECT *
        FROM orders
        WHERE customer_id = 5000;
    """

    analyze_query_plan(
        TEST_QUERY
    )
