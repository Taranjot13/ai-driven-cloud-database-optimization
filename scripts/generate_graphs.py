from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest

from scripts.decision_engine import get_engine
from scripts.cost_optimizer import run_cost_optimization


OUTPUT_DIR = Path("docs") / "graphs"
SLOW_QUERY_THRESHOLD_MS = 5.0

SUCCESS_DECISIONS = {
    "KEEP",
    "KEEP INDEX",
    "EXISTING INDEX VERIFIED",
}


def load_performance_data():
    engine = get_engine()

    query = """
        SELECT
            metric_id,
            execution_time_ms,
            rows_returned,
            recorded_at
        FROM query_performance
        ORDER BY metric_id;
    """

    try:
        return pd.read_sql_query(query, engine)
    finally:
        engine.dispose()


def load_optimization_history():
    engine = get_engine()

    query = """
        SELECT
            optimization_id,
            optimization_type,
            improvement_percent,
            decision,
            created_at
        FROM optimization_history
        ORDER BY optimization_id;
    """

    try:
        return pd.read_sql_query(query, engine)
    finally:
        engine.dispose()


def generate_latency_graph(df):
    plt.figure(figsize=(10, 5))

    plt.plot(
        df["metric_id"],
        df["execution_time_ms"],
        marker="o",
        linewidth=1
    )

    plt.axhline(
        SLOW_QUERY_THRESHOLD_MS,
        linestyle="--",
        linewidth=1
    )

    plt.xlabel("Metric ID")
    plt.ylabel("Execution Time (ms)")
    plt.title("Query Execution Latency Over Time")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    output = OUTPUT_DIR / "query_latency.png"
    plt.savefig(output, dpi=200)
    plt.close()

    return output


def generate_latency_distribution(df):
    plt.figure(figsize=(8, 5))

    plt.hist(
        df["execution_time_ms"],
        bins=12,
        edgecolor="black"
    )

    plt.axvline(
        SLOW_QUERY_THRESHOLD_MS,
        linestyle="--",
        linewidth=1
    )

    plt.xlabel("Execution Time (ms)")
    plt.ylabel("Frequency")
    plt.title("Distribution of Query Execution Latency")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    output = OUTPUT_DIR / "latency_distribution.png"
    plt.savefig(output, dpi=200)
    plt.close()

    return output


def generate_optimization_outcomes(history):
    counts = (
        history["decision"]
        .value_counts()
        .sort_values(ascending=False)
    )

    plt.figure(figsize=(10, 5))

    plt.bar(
        counts.index.astype(str),
        counts.values
    )

    plt.xlabel("Optimization Decision")
    plt.ylabel("Number of Records")
    plt.title("Optimization Outcome Distribution")
    plt.xticks(
        rotation=35,
        ha="right"
    )
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()

    output = OUTPUT_DIR / "optimization_outcomes.png"
    plt.savefig(output, dpi=200)
    plt.close()

    return output


def generate_successful_improvements(history):
    successful = history[
        history["decision"].isin(
            SUCCESS_DECISIONS
        )
    ].copy()

    successful["improvement_percent"] = (
        pd.to_numeric(
            successful["improvement_percent"],
            errors="coerce"
        )
    )

    successful = successful.dropna(
        subset=["improvement_percent"]
    )

    plt.figure(figsize=(10, 5))

    if successful.empty:
        plt.text(
            0.5,
            0.5,
            "No successful optimization records",
            ha="center",
            va="center"
        )
        plt.axis("off")
    else:
        plt.bar(
            successful["optimization_id"].astype(str),
            successful["improvement_percent"]
        )

        plt.axhline(
            0,
            linewidth=1
        )

        plt.xlabel("Optimization ID")
        plt.ylabel("Improvement (%)")
        plt.title(
            "Performance Improvement of Successful / Verified Optimizations"
        )
        plt.xticks(rotation=45)
        plt.grid(True, axis="y", alpha=0.3)

    plt.tight_layout()

    output = (
        OUTPUT_DIR
        / "successful_optimization_improvement.png"
    )

    plt.savefig(output, dpi=200)
    plt.close()

    return output


def generate_anomaly_graph(df):
    if len(df) < 10:
        print(
            "Not enough performance data for anomaly graph."
        )
        return None

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

    df = df.copy()

    df["anomaly"] = model.fit_predict(
        features
    )

    anomaly_mask = (
        df["anomaly"] == -1
    )

    normal_mask = (
        df["anomaly"] == 1
    )

    plt.figure(figsize=(10, 5))

    plt.scatter(
        df.loc[
            normal_mask,
            "metric_id"
        ],
        df.loc[
            normal_mask,
            "execution_time_ms"
        ],
        marker="o",
        label="Normal"
    )

    plt.scatter(
        df.loc[
            anomaly_mask,
            "metric_id"
        ],
        df.loc[
            anomaly_mask,
            "execution_time_ms"
        ],
        marker="x",
        s=60,
        label="Anomaly"
    )

    plt.xlabel("Metric ID")
    plt.ylabel("Execution Time (ms)")
    plt.title("Detected Performance Anomalies")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    output = OUTPUT_DIR / "anomaly_detection.png"
    plt.savefig(output, dpi=200)
    plt.close()

    return output


def generate_cost_graph():
    cost = run_cost_optimization()

    values = [
        cost["compute_cost"],
        cost["storage_cost"],
        cost["connection_cost"],
    ]

    labels = [
        "Compute",
        "Storage",
        "Connections",
    ]

    plt.figure(figsize=(8, 5))

    plt.bar(
        labels,
        values
    )

    plt.xlabel("Cost Component")
    plt.ylabel("Estimated Monthly Cost ($)")
    plt.title("Estimated Monthly Infrastructure Cost")
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()

    output = OUTPUT_DIR / "cost_breakdown.png"
    plt.savefig(output, dpi=200)
    plt.close()

    return output


def main():
    print("=" * 55)
    print(" GENERATING EXPERIMENT GRAPHS")
    print("=" * 55)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    performance_df = load_performance_data()
    history_df = load_optimization_history()

    if performance_df.empty:
        print(
            "\nNo performance data available."
        )
        return

    generated_files = []

    generated_files.append(
        generate_latency_graph(
            performance_df
        )
    )

    generated_files.append(
        generate_latency_distribution(
            performance_df
        )
    )

    if not history_df.empty:
        generated_files.append(
            generate_optimization_outcomes(
                history_df
            )
        )

        generated_files.append(
            generate_successful_improvements(
                history_df
            )
        )

    anomaly_graph = generate_anomaly_graph(
        performance_df
    )

    if anomaly_graph:
        generated_files.append(
            anomaly_graph
        )

    generated_files.append(
        generate_cost_graph()
    )

    print("\nGenerated graphs:")

    for file_path in generated_files:
        print(f"- {file_path}")

    print(
        "\nGraph generation completed successfully."
    )


if __name__ == "__main__":
    main()
