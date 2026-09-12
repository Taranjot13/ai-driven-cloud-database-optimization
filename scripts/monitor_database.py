import psycopg2
import time


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "cloud_optimizer",
    "user": "postgres",
    "password": "123456t"
}


DEFAULT_QUERY = """
SELECT *
FROM orders
WHERE customer_id = 5000;
"""


def monitor_query(query):
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    try:
        start_time = time.perf_counter()

        cursor.execute(query)
        results = cursor.fetchall()

        end_time = time.perf_counter()

        execution_time = (end_time - start_time) * 1000
        rows_returned = len(results)

        insert_query = """
            INSERT INTO query_performance
            (query_text, execution_time_ms, rows_returned)
            VALUES (%s, %s, %s);
        """

        cursor.execute(
            insert_query,
            (query, execution_time, rows_returned)
        )

        connection.commit()

        print("Query executed successfully.")
        print(f"Execution Time: {execution_time:.3f} ms")
        print(f"Rows Returned: {rows_returned}")
        print("Performance metric saved to database.")

        return {
            "query": query,
            "execution_time_ms": execution_time,
            "rows_returned": rows_returned
        }

    finally:
        cursor.close()
        connection.close()


def monitor_database(query=None):
    """
    Main monitoring function used by the autonomous system.
    """

    if query is None:
        query = DEFAULT_QUERY

    return monitor_query(query)


if __name__ == "__main__":
    monitor_database()