import psycopg2
import time

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "cloud_optimizer",
    "user": "postgres",
    "password": "123456t"
}


def monitor_query(query):
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

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

    cursor.close()
    connection.close()


query = """
SELECT *
FROM orders
WHERE customer_id = 5000;
"""

monitor_query(query)