import psycopg2
import re

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "cloud_optimizer",
    "user": "postgres",
    "password": "123456t"
}


def get_execution_plan(query, parameters):
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    cursor.execute(
        "EXPLAIN (ANALYZE, BUFFERS) " + query,
        parameters
    )

    plan = "\n".join(row[0] for row in cursor.fetchall())

    cursor.close()
    connection.close()

    return plan


def recommend_index(query, parameters):
    plan = get_execution_plan(query, parameters)

    print("\n===== EXECUTION PLAN =====\n")
    print(plan)

    print("\n===== INDEX ANALYSIS =====\n")

    # Detect sequential scans
    sequential_scan = re.search(
        r"Seq Scan on (\w+)",
        plan
    )

    # Detect equality filters such as:
    # Filter: (customer_id = 5000)
    filter_match = re.search(
        r"Filter:\s*\((\w+)\s*=",
        plan
    )

    if sequential_scan and filter_match:
        table = sequential_scan.group(1)
        column = filter_match.group(1)

        print("Potential optimization detected.")
        print(f"Table: {table}")
        print(f"Column: {column}")
        print(
            f"Recommendation: Create an index on "
            f"{table}({column})."
        )

    else:
        print("No automatic index recommendation generated.")


if __name__ == "__main__":

    query = """
    SELECT *
    FROM orders
    WHERE customer_id = %s;
    """

    parameters = (5000,)

    recommend_index(query, parameters)