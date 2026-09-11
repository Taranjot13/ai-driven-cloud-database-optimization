import re
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import IsolationForest

from scripts.learning_engine import get_learning_signal


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "cloud_optimizer",
    "user": "postgres",
    "password": "123456t"
}


SLOW_QUERY_THRESHOLD = 5.0
PREDICTION_RISK_THRESHOLD = 5.0


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


def load_metrics():
    engine = create_database_engine()

    query = """
        SELECT
            metric_id,
            query_text,
            execution_time_ms,
            rows_returned,
            recorded_at
        FROM query_performance
        ORDER BY recorded_at;
    """

    try:
        df = pd.read_sql_query(
            query,
            engine
        )

        return df

    finally:
        engine.dispose()


def detect_anomalies(df):
    if len(df) < 10:
        return pd.Series(
            [False] * len(df),
            index=df.index
        )

    features = df[
        [
            "execution_time_ms",
            "rows_returned"
        ]
    ]

    model = IsolationForest(
        contamination=0.10,
        random_state=42
    )

    predictions = model.fit_predict(features)

    return predictions == -1


def analyze_workload(df):
    average_latency = (
        df["execution_time_ms"].mean()
    )

    latest_latency = (
        df.iloc[-1]["execution_time_ms"]
    )

    slow_queries = df[
        df["execution_time_ms"]
        > SLOW_QUERY_THRESHOLD
    ]

    anomalies = df[
        df["is_anomaly"]
    ]

    return {
        "average_latency": average_latency,
        "latest_latency": latest_latency,
        "slow_queries": slow_queries,
        "anomalies": anomalies
    }


def extract_query_target(query_text):
    if not query_text:
        return None, None

    from_match = re.search(
        r"\bFROM\s+([A-Za-z_][A-Za-z0-9_]*)",
        query_text,
        re.IGNORECASE
    )

    where_match = re.search(
        r"\bWHERE\s+([A-Za-z_][A-Za-z0-9_]*)\s*=",
        query_text,
        re.IGNORECASE
    )

    if not from_match or not where_match:
        return None, None

    table_name = from_match.group(1)
    column_name = where_match.group(1)

    return table_name, column_name


def determine_optimization_policy(
    learning_risk
):
    """
    Determine how aggressively the system
    should perform autonomous optimization
    based on historical learning evidence.
    """

    if learning_risk == "LOW":
        return {
            "mode": "AUTONOMOUS",
            "allow_optimization": True,
            "description":
                "Historical results strongly "
                "support autonomous optimization."
        }

    if learning_risk == "MEDIUM":
        return {
            "mode": "CAUTIOUS",
            "allow_optimization": True,
            "description":
                "Optimization is allowed with "
                "strict performance verification."
        }

    if learning_risk == "INSUFFICIENT_DATA":
        return {
            "mode": "EXPLORATORY",
            "allow_optimization": True,
            "description":
                "Optimization is allowed cautiously "
                "while the system builds historical evidence."
        }

    if learning_risk == "HIGH":
        return {
            "mode": "PROTECTIVE",
            "allow_optimization": False,
            "description":
                "Previous optimization results indicate "
                "high risk. Database modification is blocked."
        }

    return {
        "mode": "PROTECTIVE",
        "allow_optimization": False,
        "description":
            "Learning state is unknown. "
            "Database modification is blocked."
    }


def make_decision(
    analysis,
    predicted_latency=None
):
    slow_queries = analysis["slow_queries"]
    anomalies = analysis["anomalies"]

    average_latency = analysis["average_latency"]
    latest_latency = analysis["latest_latency"]

    learning = get_learning_signal()

    learning_policy = determine_optimization_policy(
        learning["risk_level"]
    )

    prediction_risk = False

    if predicted_latency is not None:
        if predicted_latency > PREDICTION_RISK_THRESHOLD:
            prediction_risk = True

    print(
        "\n===== AUTONOMOUS DECISION ENGINE =====\n"
    )

    print(
        f"Average latency: "
        f"{average_latency:.3f} ms"
    )

    print(
        f"Latest latency: "
        f"{latest_latency:.3f} ms"
    )

    if predicted_latency is not None:
        print(
            f"Predicted latency: "
            f"{predicted_latency:.3f} ms"
        )
    else:
        print(
            "Predicted latency: Not available"
        )

    print(
        f"Slow queries detected: "
        f"{len(slow_queries)}"
    )

    print(
        f"ML anomalies detected: "
        f"{len(anomalies)}"
    )

    print(
        f"Prediction risk: "
        f"{'YES' if prediction_risk else 'NO'}"
    )

    print(
        f"Historical optimization success: "
        f"{learning['success_rate']:.2f}%"
    )

    print(
        f"Learning risk level: "
        f"{learning['risk_level']}"
    )

    print(
        f"Learning policy: "
        f"{learning_policy['mode']}"
    )

    print(
        f"Optimization allowed: "
        f"{'YES' if learning_policy['allow_optimization'] else 'NO'}"
    )

    print(
        "\nPolicy interpretation:"
    )

    print(
        learning_policy["description"]
    )

    print(
        "\n===== DECISION =====\n"
    )

    if len(slow_queries) > 0:

        query = slow_queries.iloc[0]

        print(
            "Problem detected: Slow query"
        )

        print(
            f"Metric ID: "
            f"{int(query['metric_id'])}"
        )

        print(
            f"Execution time: "
            f"{query['execution_time_ms']:.3f} ms"
        )

        print(
            f"Query: "
            f"{query['query_text']}"
        )

        if len(anomalies) > 0:
            print(
                "ML signal: "
                "Performance anomaly detected"
            )

        if prediction_risk:
            print(
                "Prediction signal: "
                "Future performance risk detected"
            )

        print(
            f"\nLearning signal: "
            f"{learning['risk_level']}"
        )

        print(
            f"Optimization policy: "
            f"{learning_policy['mode']}"
        )

        table_name, column_name = (
            extract_query_target(
                query["query_text"]
            )
        )

        if (
            table_name is None
            or column_name is None
        ):
            print(
                "\nUnable to safely identify "
                "an optimization target."
            )

            print(
                "Recommended action:"
            )

            print(
                "ANALYZE_WORKLOAD"
            )

            return {
                "action": "ANALYZE_WORKLOAD",
                "metric_id":
                    int(query["metric_id"]),
                "query_text":
                    query["query_text"],
                "table": None,
                "column": None,
                "predicted_latency":
                    predicted_latency,
                "learning_risk":
                    learning["risk_level"],
                "learning_policy":
                    learning_policy["mode"]
            }

        print(
            f"\nOptimization target: "
            f"{table_name}.{column_name}"
        )

        if not learning_policy[
            "allow_optimization"
        ]:

            print(
                "\nAutonomous optimization "
                "blocked by learning policy."
            )

            print(
                "The system will not modify "
                "the database."
            )

            print(
                "\nRecommended action:"
            )

            print(
                "ANALYZE_WORKLOAD"
            )

            return {
                "action": "ANALYZE_WORKLOAD",
                "metric_id":
                    int(query["metric_id"]),
                "query_text":
                    query["query_text"],
                "table":
                    table_name,
                "column":
                    column_name,
                "predicted_latency":
                    predicted_latency,
                "learning_risk":
                    learning["risk_level"],
                "learning_policy":
                    learning_policy["mode"]
            }

        print(
            "\nLearning policy permits "
            "autonomous optimization."
        )

        print(
            "The optimizer will perform "
            "performance verification "
            "and rollback when required."
        )

        print(
            "\nRecommended action:"
        )

        print(
            "OPTIMIZE_INDEX"
        )

        return {
            "action": "OPTIMIZE_INDEX",
            "metric_id":
                int(query["metric_id"]),
            "query_text":
                query["query_text"],
            "table":
                table_name,
            "column":
                column_name,
            "predicted_latency":
                predicted_latency,
            "learning_risk":
                learning["risk_level"],
            "learning_policy":
                learning_policy["mode"]
        }

    elif prediction_risk:

        print(
            "Problem detected: "
            "Predicted performance degradation"
        )

        print(
            f"Predicted execution time: "
            f"{predicted_latency:.3f} ms"
        )

        print(
            "\nRecommended action:"
        )

        print(
            "ANALYZE_WORKLOAD"
        )

        return {
            "action": "ANALYZE_WORKLOAD",
            "metric_id": None,
            "query_text": None,
            "table": None,
            "column": None,
            "predicted_latency":
                predicted_latency,
            "learning_risk":
                learning["risk_level"],
            "learning_policy":
                learning_policy["mode"]
        }

    elif len(anomalies) > 0:

        print(
            "Problem detected: "
            "Performance anomaly"
        )

        print(
            "\nRecommended action:"
        )

        print(
            "ANALYZE_WORKLOAD"
        )

        return {
            "action": "ANALYZE_WORKLOAD",
            "metric_id": None,
            "query_text": None,
            "table": None,
            "column": None,
            "predicted_latency":
                predicted_latency,
            "learning_risk":
                learning["risk_level"],
            "learning_policy":
                learning_policy["mode"]
        }

    else:

        print(
            "No significant "
            "performance problem detected."
        )

        print(
            "\nRecommended action:"
        )

        print(
            "CONTINUE_MONITORING"
        )

        return {
            "action": "MONITOR",
            "metric_id": None,
            "query_text": None,
            "table": None,
            "column": None,
            "predicted_latency":
                predicted_latency,
            "learning_risk":
                learning["risk_level"],
            "learning_policy":
                learning_policy["mode"]
        }


def main():

    df = load_metrics()

    if len(df) < 10:

        print(
            "Not enough performance data."
        )

        print(
            f"Available records: {len(df)}"
        )

        return

    df["is_anomaly"] = (
        detect_anomalies(df)
    )

    analysis = analyze_workload(df)

    decision = make_decision(
        analysis,
        predicted_latency=None
    )

    print(
        "\n===== FINAL SYSTEM DECISION ====="
    )

    print(
        f"Decision: "
        f"{decision['action']}"
    )

    print(
        f"Learning risk: "
        f"{decision['learning_risk']}"
    )

    print(
        f"Learning policy: "
        f"{decision['learning_policy']}"
    )

    if decision["table"] is not None:

        print(
            f"Optimization target: "
            f"{decision['table']}."
            f"{decision['column']}"
        )


if __name__ == "__main__":
    main()