import psycopg2


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "cloud_optimizer",
    "user": "postgres",
    "password": "123456t"  # Replace with your actual PostgreSQL password
}


# Cloud-agnostic reference pricing model.
# These values are estimates for project evaluation, not
# provider-specific production pricing.
MONTHLY_COMPUTE_BASE_COST = 50.0
MONTHLY_STORAGE_COST_PER_GB = 0.10
MONTHLY_CONNECTION_COST = 0.05

STORAGE_WARNING_GB = 10.0
CONNECTION_WARNING_PERCENT = 70.0
CACHE_WARNING_PERCENT = 90.0


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def load_resource_metrics():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT
                (SELECT count(*) FROM pg_stat_activity),
                current_setting('max_connections')::INTEGER,
                pg_database_size(current_database()) / 1024.0 / 1024.0 / 1024.0,
                (
                    SELECT
                        CASE
                            WHEN (blks_hit + blks_read) = 0 THEN 100.0
                            ELSE blks_hit * 100.0 / (blks_hit + blks_read)
                        END
                    FROM pg_stat_database
                    WHERE datname = current_database()
                );
            """
        )

        active_connections, max_connections, database_size_gb, cache_hit_ratio = (
            cursor.fetchone()
        )

        return {
            "active_connections": int(active_connections or 0),
            "max_connections": int(max_connections or 1),
            "database_size_gb": float(database_size_gb or 0.0),
            "cache_hit_ratio": float(cache_hit_ratio or 0.0),
        }

    finally:
        cursor.close()
        connection.close()


def calculate_cost(metrics):
    active_connections = metrics["active_connections"]
    max_connections = metrics["max_connections"]
    database_size_gb = metrics["database_size_gb"]

    connection_utilization = (
        active_connections / max_connections * 100
        if max_connections > 0
        else 0
    )

    compute_cost = MONTHLY_COMPUTE_BASE_COST

    storage_cost = (
        database_size_gb * MONTHLY_STORAGE_COST_PER_GB
    )

    connection_cost = (
        active_connections * MONTHLY_CONNECTION_COST
    )

    estimated_monthly_cost = (
        compute_cost +
        storage_cost +
        connection_cost
    )

    return {
        "compute_cost": compute_cost,
        "storage_cost": storage_cost,
        "connection_cost": connection_cost,
        "estimated_monthly_cost": estimated_monthly_cost,
        "connection_utilization": connection_utilization,
    }


def determine_cost_status(metrics, costs):
    recommendations = []

    database_size_gb = metrics["database_size_gb"]
    cache_hit_ratio = metrics["cache_hit_ratio"]
    connection_utilization = costs["connection_utilization"]

    if connection_utilization >= CONNECTION_WARNING_PERCENT:
        recommendations.append(
            "Connection utilization is high. Consider connection pooling "
            "and workload optimization."
        )

    if database_size_gb >= STORAGE_WARNING_GB:
        recommendations.append(
            "Database storage usage is high. Consider archiving or "
            "retention policies for historical data."
        )

    if cache_hit_ratio < CACHE_WARNING_PERCENT:
        recommendations.append(
            "Cache hit ratio is below the target level. Query and cache "
            "configuration should be reviewed."
        )

    if not recommendations:
        recommendations.append(
            "Resource utilization is currently cost-efficient."
        )

    if (
        connection_utilization >= 90
        or database_size_gb >= STORAGE_WARNING_GB * 2
    ):
        status = "HIGH_COST_RISK"
    elif (
        connection_utilization >= CONNECTION_WARNING_PERCENT
        or database_size_gb >= STORAGE_WARNING_GB
        or cache_hit_ratio < CACHE_WARNING_PERCENT
    ):
        status = "COST_WARNING"
    else:
        status = "COST_EFFICIENT"

    return status, recommendations


def run_cost_optimization():
    metrics = load_resource_metrics()
    costs = calculate_cost(metrics)

    status, recommendations = determine_cost_status(
        metrics,
        costs
    )

    result = {
        "status": status,
        "active_connections": metrics["active_connections"],
        "max_connections": metrics["max_connections"],
        "connection_utilization": costs["connection_utilization"],
        "cache_hit_ratio": metrics["cache_hit_ratio"],
        "database_size_gb": metrics["database_size_gb"],
        "compute_cost": costs["compute_cost"],
        "storage_cost": costs["storage_cost"],
        "connection_cost": costs["connection_cost"],
        "estimated_monthly_cost": costs["estimated_monthly_cost"],
        "recommendations": recommendations,
    }

    return result


def print_cost_analysis(result):
    print("\n===== COST OPTIMIZATION =====")

    print(
        f"Estimated monthly compute cost: "
        f"${result['compute_cost']:.2f}"
    )

    print(
        f"Estimated monthly storage cost: "
        f"${result['storage_cost']:.2f}"
    )

    print(
        f"Estimated monthly connection cost: "
        f"${result['connection_cost']:.2f}"
    )

    print(
        f"Estimated monthly total cost: "
        f"${result['estimated_monthly_cost']:.2f}"
    )

    print(
        f"Database size: "
        f"{result['database_size_gb']:.4f} GB"
    )

    print(
        f"Connection utilization: "
        f"{result['connection_utilization']:.2f}%"
    )

    print(
        f"Cache hit ratio: "
        f"{result['cache_hit_ratio']:.2f}%"
    )

    print(
        f"Cost status: "
        f"{result['status']}"
    )

    print("\nCost recommendations:")

    for recommendation in result["recommendations"]:
        print(f"- {recommendation}")


def main():
    result = run_cost_optimization()
    print_cost_analysis(result)


if __name__ == "__main__":
    main()