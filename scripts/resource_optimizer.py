import psycopg2
from datetime import datetime


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "cloud_optimizer",
    "user": "postgres",
    "password": "123456t"  # Replace with your actual PostgreSQL password   
}


# Resource health thresholds
CONNECTION_WARNING_PERCENT = 70.0
CONNECTION_CRITICAL_PERCENT = 90.0

CACHE_WARNING_PERCENT = 90.0
CACHE_CRITICAL_PERCENT = 80.0

ROLLBACK_WARNING_PERCENT = 10.0
ROLLBACK_CRITICAL_PERCENT = 30.0

DATABASE_SIZE_WARNING_GB = 10.0


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def get_connection_resources(cursor):
    cursor.execute("""
        SELECT
            COUNT(*)
        FROM pg_stat_activity
        WHERE datname = current_database();
    """)

    active_connections = cursor.fetchone()[0]

    cursor.execute("""
        SELECT setting
        FROM pg_settings
        WHERE name = 'max_connections';
    """)

    max_connections = int(cursor.fetchone()[0])

    connection_utilization = (
        active_connections / max_connections
    ) * 100

    return {
        "active_connections": active_connections,
        "max_connections": max_connections,
        "connection_utilization": connection_utilization
    }


def get_cache_resources(cursor):
    cursor.execute("""
        SELECT
            COALESCE(
                SUM(blks_hit) * 100.0 /
                NULLIF(SUM(blks_hit + blks_read), 0),
                0
            )
        FROM pg_stat_database
        WHERE datname = current_database();
    """)

    cache_hit_ratio = float(cursor.fetchone()[0] or 0)

    return {
        "cache_hit_ratio": cache_hit_ratio
    }


def get_transaction_health(cursor):
    cursor.execute("""
        SELECT
            xact_commit,
            xact_rollback
        FROM pg_stat_database
        WHERE datname = current_database();
    """)

    result = cursor.fetchone()

    if result is None:
        return {
            "committed_transactions": 0,
            "rollback_transactions": 0,
            "rollback_rate": 0.0
        }

    committed_transactions = int(result[0] or 0)
    rollback_transactions = int(result[1] or 0)

    total_transactions = (
        committed_transactions +
        rollback_transactions
    )

    if total_transactions == 0:
        rollback_rate = 0.0
    else:
        rollback_rate = (
            rollback_transactions /
            total_transactions
        ) * 100

    return {
        "committed_transactions": committed_transactions,
        "rollback_transactions": rollback_transactions,
        "rollback_rate": rollback_rate
    }


def get_database_size(cursor):
    cursor.execute("""
        SELECT pg_database_size(current_database());
    """)

    size_bytes = cursor.fetchone()[0]

    database_size_gb = (
        size_bytes /
        (1024 ** 3)
    )

    return {
        "database_size_gb": database_size_gb
    }


def get_memory_configuration(cursor):
    cursor.execute("""
        SELECT name, setting
        FROM pg_settings
        WHERE name IN (
            'shared_buffers',
            'work_mem',
            'effective_cache_size'
        )
        ORDER BY name;
    """)

    configuration = {}

    for name, setting in cursor.fetchall():
        configuration[name] = setting

    return configuration


def determine_resource_status(
    connection_utilization,
    cache_hit_ratio,
    rollback_rate,
    database_size_gb
):
    critical_conditions = 0
    warning_conditions = 0

    # Connection pressure
    if connection_utilization >= CONNECTION_CRITICAL_PERCENT:
        critical_conditions += 1
    elif connection_utilization >= CONNECTION_WARNING_PERCENT:
        warning_conditions += 1

    # Cache health
    if cache_hit_ratio < CACHE_CRITICAL_PERCENT:
        critical_conditions += 1
    elif cache_hit_ratio < CACHE_WARNING_PERCENT:
        warning_conditions += 1

    # Rollback activity
    #
    # Rollbacks are treated as a warning signal rather than
    # an automatic critical infrastructure failure because
    # controlled optimization experiments can intentionally
    # generate rollback activity.
    if rollback_rate >= ROLLBACK_CRITICAL_PERCENT:
        warning_conditions += 1
    elif rollback_rate >= ROLLBACK_WARNING_PERCENT:
        warning_conditions += 1

    # Database size
    if database_size_gb >= DATABASE_SIZE_WARNING_GB:
        warning_conditions += 1

    # Critical requires a genuine resource-pressure condition.
    if critical_conditions > 0:
        return "CRITICAL"

    if warning_conditions > 0:
        return "WARNING"

    return "HEALTHY"


def build_recommendations(
    status,
    connection_utilization,
    cache_hit_ratio,
    rollback_rate,
    database_size_gb
):
    recommendations = []

    if connection_utilization >= CONNECTION_CRITICAL_PERCENT:
        recommendations.append(
            "CRITICAL: Connection utilization is very high. "
            "Investigate connection pooling and maximum connections."
        )
    elif connection_utilization >= CONNECTION_WARNING_PERCENT:
        recommendations.append(
            "WARNING: Connection utilization is elevated. "
            "Monitor connection usage and pooling."
        )

    if cache_hit_ratio < CACHE_CRITICAL_PERCENT:
        recommendations.append(
            "CRITICAL: Cache hit ratio is low. "
            "Investigate memory configuration and query access patterns."
        )
    elif cache_hit_ratio < CACHE_WARNING_PERCENT:
        recommendations.append(
            "WARNING: Cache hit ratio is below the recommended level."
        )

    if rollback_rate >= ROLLBACK_CRITICAL_PERCENT:
        recommendations.append(
            "WARNING: Transaction rollback rate is high. "
            "Investigate failed transactions and application errors. "
            "Controlled optimizer rollbacks may contribute to this metric."
        )
    elif rollback_rate >= ROLLBACK_WARNING_PERCENT:
        recommendations.append(
            "WARNING: Transaction rollback activity is elevated. "
            "Monitor application and optimizer transaction behavior."
        )

    if database_size_gb >= DATABASE_SIZE_WARNING_GB:
        recommendations.append(
            "WARNING: Database size is large. "
            "Review storage growth and retention policies."
        )

    if not recommendations:
        recommendations.append(
            "Database resource utilization is within healthy limits."
        )

    return recommendations


def run_resource_optimization():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        connection_resources = get_connection_resources(cursor)
        cache_resources = get_cache_resources(cursor)
        transaction_health = get_transaction_health(cursor)
        database_size = get_database_size(cursor)
        memory_configuration = get_memory_configuration(cursor)

        active_connections = connection_resources[
            "active_connections"
        ]

        max_connections = connection_resources[
            "max_connections"
        ]

        connection_utilization = connection_resources[
            "connection_utilization"
        ]

        cache_hit_ratio = cache_resources[
            "cache_hit_ratio"
        ]

        rollback_rate = transaction_health[
            "rollback_rate"
        ]

        database_size_gb = database_size[
            "database_size_gb"
        ]

        resource_status = determine_resource_status(
            connection_utilization,
            cache_hit_ratio,
            rollback_rate,
            database_size_gb
        )

        recommendations = build_recommendations(
            resource_status,
            connection_utilization,
            cache_hit_ratio,
            rollback_rate,
            database_size_gb
        )

        result = {
            "status": resource_status,
            "overall_status": resource_status,

            "active_connections": active_connections,
            "max_connections": max_connections,
            "connection_utilization": connection_utilization,

            "cache_hit_ratio": cache_hit_ratio,

            "committed_transactions":
                transaction_health["committed_transactions"],

            "rollback_transactions":
                transaction_health["rollback_transactions"],

            "rollback_rate": rollback_rate,

            "database_size_gb": database_size_gb,

            "memory_configuration": memory_configuration,

            "recommendations": recommendations
        }

        return result

    finally:
        cursor.close()
        connection.close()


def print_resource_analysis(result):
    print("\n========================================")
    print("     DATABASE RESOURCE OPTIMIZATION")
    print("========================================")

    print(
        f"\nTimestamp: "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print("\n--- CONNECTION RESOURCES ---")
    print(
        f"Active connections: "
        f"{result['active_connections']}"
    )
    print(
        f"Maximum connections: "
        f"{result['max_connections']}"
    )
    print(
        f"Connection utilization: "
        f"{result['connection_utilization']:.2f}%"
    )

    print("\n--- CACHE RESOURCES ---")
    print(
        f"Cache hit ratio: "
        f"{result['cache_hit_ratio']:.2f}%"
    )

    print("\n--- TRANSACTION HEALTH ---")
    print(
        f"Rollback rate: "
        f"{result['rollback_rate']:.2f}%"
    )

    print("\n--- DATABASE SIZE ---")
    print(
        f"Database size: "
        f"{result['database_size_gb']:.4f} GB"
    )

    print("\n--- MEMORY CONFIGURATION ---")

    memory = result["memory_configuration"]

    print(
        f"Shared buffers: "
        f"{memory.get('shared_buffers', 'Unknown')}"
    )
    print(
        f"Work memory: "
        f"{memory.get('work_mem', 'Unknown')}"
    )
    print(
        f"Effective cache size: "
        f"{memory.get('effective_cache_size', 'Unknown')}"
    )

    print("\n--- RESOURCE STATUS ---")
    print(
        f"Overall status: "
        f"{result['status']}"
    )

    print("\n--- OPTIMIZATION RECOMMENDATIONS ---")

    for index, recommendation in enumerate(
        result["recommendations"],
        start=1
    ):
        print(f"{index}. {recommendation}")

    print("\n========================================")
    print("Resource analysis completed.")
    print("========================================")


def main():
    result = run_resource_optimization()
    print_resource_analysis(result)


if __name__ == "__main__":
    main()