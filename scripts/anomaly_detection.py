import psycopg2
import pandas as pd
from sklearn.ensemble import IsolationForest

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "cloud_optimizer",
    "user": "postgres",
    "password": "123456t"
}


def load_metrics():
    connection = psycopg2.connect(**DB_CONFIG)

    query = """
        SELECT
            metric_id,
            execution_time_ms,
            rows_returned
        FROM query_performance
        ORDER BY recorded_at;
    """

    df = pd.read_sql_query(query, connection)

    connection.close()

    return df


def detect_anomalies():

    df = load_metrics()

    if len(df) < 10:
        print("Not enough performance data for anomaly detection.")
        print(f"Currently available records: {len(df)}")
        return

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

    df["anomaly"] = model.fit_predict(features)

    df["status"] = df["anomaly"].map({
        1: "Normal",
        -1: "Anomaly"
    })

    print("\n===== AI ANOMALY DETECTION =====\n")

    print(df[
        [
            "metric_id",
            "execution_time_ms",
            "rows_returned",
            "status"
        ]
    ].to_string(index=False))

    anomalies = df[df["anomaly"] == -1]

    print("\n===== DETECTED ANOMALIES =====")
    print(f"Anomalies detected: {len(anomalies)}")

    if len(anomalies) > 0:
        print(
            anomalies[
                [
                    "metric_id",
                    "execution_time_ms",
                    "rows_returned"
                ]
            ].to_string(index=False)
        )


if __name__ == "__main__":
    detect_anomalies()