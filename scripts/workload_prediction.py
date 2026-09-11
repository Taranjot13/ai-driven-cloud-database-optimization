import psycopg2
import pandas as pd
from sklearn.ensemble import RandomForestRegressor


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
            rows_returned,
            recorded_at
        FROM query_performance
        ORDER BY recorded_at;
    """

    df = pd.read_sql_query(query, connection)

    connection.close()

    return df


def predict_next_execution_time(df):

    if len(df) < 10:
        return None

    df["recorded_at"] = pd.to_datetime(
        df["recorded_at"]
    )

    df["time_index"] = range(len(df))

    df["hour"] = df["recorded_at"].dt.hour
    df["minute"] = df["recorded_at"].dt.minute
    df["second"] = df["recorded_at"].dt.second

    features = [
        "time_index",
        "hour",
        "minute",
        "second",
        "rows_returned"
    ]

    X = df[features]
    y = df["execution_time_ms"]

    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42
    )

    model.fit(X, y)

    latest = df.iloc[-1]

    next_index = len(df)

    prediction_input = pd.DataFrame(
        [{
            "time_index": next_index,
            "hour": latest["hour"],
            "minute": latest["minute"],
            "second": latest["second"],
            "rows_returned": latest["rows_returned"]
        }]
    )

    prediction = model.predict(
        prediction_input
    )[0]

    return prediction


def run_prediction():

    df = load_metrics()

    if len(df) < 10:

        print(
            "Not enough performance data "
            "for workload prediction."
        )

        return None

    prediction = predict_next_execution_time(df)

    average_latency = df[
        "execution_time_ms"
    ].mean()

    maximum_latency = df[
        "execution_time_ms"
    ].max()

    print("\n===== WORKLOAD PREDICTION =====\n")

    print(
        f"Historical observations: {len(df)}"
    )

    print(
        f"Average execution time: "
        f"{average_latency:.3f} ms"
    )

    print(
        f"Maximum execution time: "
        f"{maximum_latency:.3f} ms"
    )

    print(
        f"Predicted next execution time: "
        f"{prediction:.3f} ms"
    )

    if prediction > average_latency:

        print(
            "\nPrediction: Potential "
            "performance degradation detected."
        )

    else:

        print(
            "\nPrediction: Expected "
            "performance within normal range."
        )

    return prediction


if __name__ == "__main__":
    run_prediction()