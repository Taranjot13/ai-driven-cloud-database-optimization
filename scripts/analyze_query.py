import psycopg2

from scripts.db_config import DB_CONFIG



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