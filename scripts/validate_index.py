import psycopg2
import time

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "cloud_optimizer",
    "user": "postgres",
    "password": "123456t"
}

TABLE_NAME = "orders"
COLUMN_NAME = "customer_id"
INDEX_NAME = "idx_orders_customer_id"


def execute_query(query, parameters):
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    start = time.perf_counter()

    cursor.execute(query, parameters)
    results = cursor.fetchall()

    end = time.perf_counter()

    execution_time = (end - start) * 1000

    cursor.close()
    connection.close()

    return execution_time, len(results)


def validate_index():

    query = """
        SELECT *
        FROM orders
        WHERE customer_id = %s;
    """

    parameters = (5000,)

    print("\n===== BEFORE OPTIMIZATION =====")

    before_time, before_rows = execute_query(
        query,
        parameters
    )

    print(f"Execution Time: {before_time:.3f} ms")
    print(f"Rows Returned: {before_rows}")

    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    print("\nCreating recommended index...")

    cursor.execute(
        f"""
        CREATE INDEX IF NOT EXISTS {INDEX_NAME}
        ON {TABLE_NAME}({COLUMN_NAME});
        """
    )

    connection.commit()

    cursor.close()
    connection.close()

    print("Index created successfully.")

    print("\n===== AFTER OPTIMIZATION =====")

    after_time, after_rows = execute_query(
        query,
        parameters
    )

    print(f"Execution Time: {after_time:.3f} ms")
    print(f"Rows Returned: {after_rows}")

    improvement = (
        (before_time - after_time)
        / before_time
    ) * 100

    print(f"\nPerformance Improvement: {improvement:.2f}%")

    if after_time < before_time:
        print("RESULT: Optimization successful.")
    else:
        print("RESULT: Optimization did not improve performance.")


if __name__ == "__main__":
    validate_index()