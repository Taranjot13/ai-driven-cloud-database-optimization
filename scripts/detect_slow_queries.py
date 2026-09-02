import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "cloud_optimizer",
    "user": "postgres",
    "password": "123456t"
}

SLOW_QUERY_THRESHOLD_MS = 5.0


def detect_slow_queries():
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    query = """
        SELECT
            metric_id,
            query_text,
            execution_time_ms,
            rows_returned,
            recorded_at
        FROM query_performance
        WHERE execution_time_ms > %s
        ORDER BY execution_time_ms DESC;
    """

    cursor.execute(query, (SLOW_QUERY_THRESHOLD_MS,))
    slow_queries = cursor.fetchall()

    print("\n===== SLOW QUERY REPORT =====")
    print(f"Threshold: {SLOW_QUERY_THRESHOLD_MS} ms")
    print(f"Slow queries found: {len(slow_queries)}\n")

    for row in slow_queries:
        metric_id, query_text, execution_time, rows, recorded_at = row

        print(f"Metric ID: {metric_id}")
        print(f"Execution Time: {execution_time:.3f} ms")
        print(f"Rows Returned: {rows}")
        print(f"Recorded At: {recorded_at}")
        print("Query:")
        print(query_text.strip())
        print("-" * 60)

    cursor.close()
    connection.close()


if __name__ == "__main__":
    detect_slow_queries()