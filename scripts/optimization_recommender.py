import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "cloud_optimizer",
    "user": "postgres",
    "password": "123456t"
}


def recommend_optimization():
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    query = """
        SELECT
            metric_id,
            query_text,
            execution_time_ms,
            rows_returned
        FROM query_performance
        WHERE execution_time_ms > 5
        ORDER BY execution_time_ms DESC;
    """

    cursor.execute(query)
    slow_queries = cursor.fetchall()

    print("\n===== OPTIMIZATION RECOMMENDATIONS =====\n")

    for metric_id, query_text, execution_time, rows_returned in slow_queries:

        query_lower = query_text.lower()

        print(f"Metric ID: {metric_id}")
        print(f"Execution Time: {execution_time:.3f} ms")
        print(f"Rows Returned: {rows_returned}")

        if "where o.customer_id" in query_lower:
            print("Recommendation:")
            print("Create an index on orders(customer_id).")

        elif "where customer_id" in query_lower:
            print("Recommendation:")
            print("Create an index on orders(customer_id).")

        elif "where category" in query_lower:
            print("Recommendation:")
            print("Create an index on products(category).")

        else:
            print("Recommendation:")
            print("Analyze the query execution plan using EXPLAIN ANALYZE.")

        print("-" * 60)

    cursor.close()
    connection.close()


if __name__ == "__main__":
    recommend_optimization()