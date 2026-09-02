import psycopg2
import time

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "cloud_optimizer",
    "user": "postgres",
    "password": "123456t"
}

INDEX_NAME = "idx_orders_customer_id"

QUERY = """
SELECT *
FROM orders
WHERE customer_id = %s;
"""

PARAMETERS = (5000,)


def execute_query():
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    start = time.perf_counter()

    cursor.execute(QUERY, PARAMETERS)
    results = cursor.fetchall()

    end = time.perf_counter()

    execution_time = (end - start) * 1000

    cursor.close()
    connection.close()

    return execution_time, len(results)


def create_index():
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    cursor.execute(
        f"""
        CREATE INDEX IF NOT EXISTS {INDEX_NAME}
        ON orders(customer_id);
        """
    )

    connection.commit()

    cursor.close()
    connection.close()


def rollback_index():
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    cursor.execute(
        f"DROP INDEX IF EXISTS {INDEX_NAME};"
    )

    connection.commit()

    cursor.close()
    connection.close()


def safe_optimization():

    print("\n===== BASELINE =====")

    before_time, before_rows = execute_query()

    print(f"Execution Time: {before_time:.3f} ms")
    print(f"Rows Returned: {before_rows}")

    print("\n===== APPLYING OPTIMIZATION =====")

    create_index()

    print("Index created.")

    print("\n===== VERIFYING OPTIMIZATION =====")

    after_time, after_rows = execute_query()

    print(f"Execution Time: {after_time:.3f} ms")
    print(f"Rows Returned: {after_rows}")

    improvement = (
        (before_time - after_time)
        / before_time
    ) * 100

    print(f"\nPerformance Change: {improvement:.2f}%")

    if after_time < before_time:
        print("\nRESULT: Optimization successful.")
        print("ACTION: Keep the index.")

    else:
        print("\nRESULT: Optimization failed.")
        print("ACTION: Rolling back index...")

        rollback_index()

        print("Rollback completed.")


if __name__ == "__main__":
    safe_optimization()