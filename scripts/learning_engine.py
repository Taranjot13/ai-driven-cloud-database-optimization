import pandas as pd
from sqlalchemy import create_engine


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "cloud_optimizer",
    "user": "postgres",
    "password": "123456t"
}


OPTIMIZATION_DECISIONS = {
    "KEEP INDEX",
    "ROLLBACK"
}


def create_database_engine():
    database_url = (
        f"postgresql+psycopg2://"
        f"{DB_CONFIG['user']}:"
        f"{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}:"
        f"{DB_CONFIG['port']}/"
        f"{DB_CONFIG['database']}"
    )

    return create_engine(database_url)


def load_optimization_history():
    engine = create_database_engine()

    query = """
        SELECT
            optimization_id,
            metric_id,
            optimization_type,
            table_name,
            column_name,
            baseline_time_ms,
            optimized_time_ms,
            improvement_percent,
            decision,
            created_at
        FROM optimization_history
        ORDER BY created_at;
    """

    try:
        return pd.read_sql_query(
            query,
            engine
        )

    finally:
        engine.dispose()


def get_learning_signal():

    df = load_optimization_history()

    if len(df) == 0:
        return {
            "total_attempts": 0,
            "successful": 0,
            "successful_optimizations": 0,
            "rollbacks": 0,
            "success_rate": 0.0,
            "average_improvement": 0.0,
            "verified_existing_indexes": 0,
            "unverified_existing_indexes": 0,
            "risk_level": "UNKNOWN"
        }

    optimization_attempts = df[
        df["decision"].isin(
            OPTIMIZATION_DECISIONS
        )
    ].copy()

    successful = len(
        optimization_attempts[
            optimization_attempts["decision"]
            == "KEEP INDEX"
        ]
    )

    rollbacks = len(
        optimization_attempts[
            optimization_attempts["decision"]
            == "ROLLBACK"
        ]
    )

    total_attempts = len(
        optimization_attempts
    )

    verified_existing_indexes = len(
        df[
            df["decision"]
            == "EXISTING INDEX VERIFIED"
        ]
    )

    unverified_existing_indexes = len(
        df[
            df["decision"]
            == "EXISTING INDEX NOT VERIFIED"
        ]
    )

    if total_attempts > 0:
        success_rate = (
            successful
            / total_attempts
        ) * 100
    else:
        success_rate = 0.0

    if total_attempts > 0:
        average_improvement = (
            optimization_attempts[
                "improvement_percent"
            ].mean()
        )
    else:
        average_improvement = 0.0

    if total_attempts < 3:
        risk_level = "INSUFFICIENT_DATA"

    elif success_rate >= 80:
        risk_level = "LOW"

    elif success_rate >= 50:
        risk_level = "MEDIUM"

    else:
        risk_level = "HIGH"

    return {
        "total_attempts": total_attempts,

        # Original key
        "successful": successful,

        # Compatibility key expected by main.py
        "successful_optimizations": successful,

        "rollbacks": rollbacks,
        "success_rate": success_rate,
        "average_improvement": average_improvement,

        "verified_existing_indexes":
            verified_existing_indexes,

        "unverified_existing_indexes":
            unverified_existing_indexes,

        "risk_level": risk_level
    }


def analyze_learning_history():

    learning = get_learning_signal()

    print("\n")
    print("=" * 70)
    print(" AI OPTIMIZATION LEARNING ENGINE ")
    print("=" * 70)

    print(
        f"\nOptimization attempts: "
        f"{learning['total_attempts']}"
    )

    print(
        f"Successful optimizations: "
        f"{learning['successful_optimizations']}"
    )

    print(
        f"Rollbacks: "
        f"{learning['rollbacks']}"
    )

    print(
        f"Success rate: "
        f"{learning['success_rate']:.2f}%"
    )

    print(
        f"Average improvement: "
        f"{learning['average_improvement']:.2f}%"
    )

    print(
        f"Existing indexes verified: "
        f"{learning['verified_existing_indexes']}"
    )

    print(
        f"Existing indexes not verified: "
        f"{learning['unverified_existing_indexes']}"
    )

    print(
        f"Learning risk level: "
        f"{learning['risk_level']}"
    )

    print(
        "\n===== LEARNING DECISION ====="
    )

    if learning["risk_level"] == "LOW":

        print(
            "Historical evidence supports "
            "continued autonomous optimization."
        )

    elif learning["risk_level"] == "MEDIUM":

        print(
            "Optimization has mixed "
            "historical results."
        )

    elif learning["risk_level"] == "HIGH":

        print(
            "Previous autonomous optimizations "
            "frequently failed."
        )

    else:

        print(
            "More autonomous optimization history "
            "is required."
        )

    print(
        "\n===== LEARNING INTERPRETATION ====="
    )

    if learning["verified_existing_indexes"] > 0:

        print(
            "Existing indexes have been evaluated "
            "without treating them as new "
            "optimizations."
        )

    if learning["unverified_existing_indexes"] > 0:

        print(
            "Some existing-index measurements were "
            "not sufficiently stable or beneficial."
        )

        print(
            "No destructive action was taken "
            "against those existing indexes."
        )

    return learning


if __name__ == "__main__":
    analyze_learning_history()