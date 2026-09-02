import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "cloud_optimizer",
    "user": "postgres",
    "password": "123456t"
}


def analyze_query(query, parameters):
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    explain_query = """
        EXPLAIN (ANALYZE, BUFFERS)
    """ + query

    cursor.execute(explain_query, parameters)

    plan = cursor.fetchall()

    print("\n===== QUERY EXECUTION PLAN =====\n")

    for row in plan:
        print(row[0])

    cursor.close()
    connection.close()


query = """
SELECT *
FROM orders
WHERE customer_id = %s;
"""

parameters = (5000,)

analyze_query(query, parameters)