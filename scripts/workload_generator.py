import psycopg2
import random
import time

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "cloud_optimizer",
    "user": "postgres",
    "password": "123456t"
}


QUERIES = [
    """
    SELECT *
    FROM orders
    WHERE customer_id = %s;
    """,

    """
    SELECT *
    FROM products
    WHERE category = %s;
    """,

    """
    SELECT *
    FROM customers
    WHERE city = %s;
    """,

    """
    SELECT o.order_id, o.order_date, o.status, o.total_amount
    FROM orders o
    WHERE o.customer_id = %s
    ORDER BY o.order_date DESC;
    """,

    """
    SELECT
        o.order_id,
        c.first_name,
        c.last_name,
        o.total_amount
    FROM orders o
    JOIN customers c
        ON o.customer_id = c.customer_id
    WHERE o.customer_id = %s;
    """
]


PARAMETERS = [
    (random.randint(1, 10000),),
    (random.choice(["Electronics", "Clothing", "Books", "Home", "Sports"]),),
    (random.choice(["New York", "London", "Toronto", "Delhi", "Mumbai"]),),
    (random.randint(1, 10000),),
    (random.randint(1, 10000),)
]


def run_workload():
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    for i in range(50):

        query_index = random.randrange(len(QUERIES))
        query = QUERIES[query_index]
        parameter = PARAMETERS[query_index]

        start_time = time.perf_counter()

        cursor.execute(query, parameter)
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

        print(
            f"Query {i + 1}/50 | "
            f"Execution Time: {execution_time:.3f} ms | "
            f"Rows: {rows_returned}"
        )

        time.sleep(0.1)

    cursor.close()
    connection.close()

    print("\nWorkload generation completed.")


if __name__ == "__main__":
    run_workload()