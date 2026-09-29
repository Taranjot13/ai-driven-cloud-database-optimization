from pathlib import Path

import pandas as pd
from sklearn.ensemble import IsolationForest

from scripts.decision_engine import get_engine
from scripts.resource_optimizer import run_resource_optimization
from scripts.cost_optimizer import run_cost_optimization
from scripts.learning_engine import get_learning_signal


OUTPUT_FILE = Path("docs/EXPERIMENT_RESULTS.md")
SLOW_QUERY_THRESHOLD_MS = 5.0

SUCCESS_DECISIONS = {
    "KEEP",
    "KEEP INDEX",
    "EXISTING INDEX VERIFIED",
}

NEUTRAL_DECISIONS = {
    "EXISTING INDEX",
}

UNSUCCESSFUL_DECISIONS = {
    "ROLLBACK",
    "EXISTING INDEX NOT VERIFIED",
    "MEASUREMENT UNSTABLE",
}


def load_performance_data():
    engine = get_engine()

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
        return pd.read_sql_query(query, engine)
    finally:
        engine.dispose()


def load_optimization_history():
    engine = get_engine()

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
        return pd.read_sql_query(query, engine)
    finally:
        engine.dispose()


def detect_anomaly_count(df):
    if len(df) < 10:
        return 0

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

    return int((predictions == -1).sum())


def calculate_performance_statistics(df):
    return {
        "observations": len(df),
        "average": float(df["execution_time_ms"].mean()),
        "median": float(df["execution_time_ms"].median()),
        "p95": float(
            df["execution_time_ms"].quantile(0.95)
        ),
        "p99": float(
            df["execution_time_ms"].quantile(0.99)
        ),
        "minimum": float(df["execution_time_ms"].min()),
        "maximum": float(df["execution_time_ms"].max()),
        "slow_queries": int(
            (
                df["execution_time_ms"]
                > SLOW_QUERY_THRESHOLD_MS
            ).sum()
        ),
    }


def calculate_optimization_statistics(history):
    if history.empty:
        return {
            "attempts": 0,
            "successful": 0,
            "neutral": 0,
            "unsuccessful": 0,
            "rollbacks": 0,
            "success_rate": 0.0,
            "average_successful_improvement": 0.0,
            "overall_average_improvement": 0.0,
            "verified_existing_indexes": 0,
        }

    history = history.copy()

    history["improvement_percent"] = pd.to_numeric(
        history["improvement_percent"],
        errors="coerce"
    )

    attempts = len(history)

    successful_mask = history["decision"].isin(
        SUCCESS_DECISIONS
    )

    neutral_mask = history["decision"].isin(
        NEUTRAL_DECISIONS
    )

    unsuccessful_mask = history["decision"].isin(
        UNSUCCESSFUL_DECISIONS
    )

    successful = int(successful_mask.sum())
    neutral = int(neutral_mask.sum())
    unsuccessful = int(unsuccessful_mask.sum())

    rollbacks = int(
        (
            history["decision"] == "ROLLBACK"
        ).sum()
    )

    success_rate = (
        (successful / attempts) * 100
        if attempts > 0
        else 0.0
    )

    successful_improvements = (
        history.loc[
            successful_mask,
            "improvement_percent"
        ]
        .dropna()
    )

    average_successful_improvement = (
        float(successful_improvements.mean())
        if not successful_improvements.empty
        else 0.0
    )

    all_improvements = (
        history["improvement_percent"]
        .dropna()
    )

    overall_average_improvement = (
        float(all_improvements.mean())
        if not all_improvements.empty
        else 0.0
    )

    verified_existing_indexes = int(
        (
            history["decision"]
            == "EXISTING INDEX VERIFIED"
        ).sum()
    )

    return {
        "attempts": attempts,
        "successful": successful,
        "neutral": neutral,
        "unsuccessful": unsuccessful,
        "rollbacks": rollbacks,
        "success_rate": success_rate,
        "average_successful_improvement":
            average_successful_improvement,
        "overall_average_improvement":
            overall_average_improvement,
        "verified_existing_indexes":
            verified_existing_indexes,
    }


def build_decision_breakdown(history):
    if history.empty:
        return pd.DataFrame(
            columns=[
                "decision",
                "attempts",
                "average_improvement"
            ]
        )

    breakdown = (
        history.groupby("decision", as_index=False)
        .agg(
            attempts=("decision", "size"),
            average_improvement=(
                "improvement_percent",
                "mean"
            )
        )
        .sort_values(
            "attempts",
            ascending=False
        )
    )

    return breakdown


def build_report(
    performance_stats,
    anomaly_count,
    optimization_stats,
    learning,
    resource,
    cost,
    top_slow_queries,
    decision_breakdown
):
    lines = []

    lines.append(
        "# Experiment Results"
    )
    lines.append("")

    lines.append(
        "This document summarizes the current "
        "experimental results generated from the "
        "PostgreSQL performance and optimization "
        "history of the AI-Driven Autonomous Cloud "
        "Database Optimization System."
    )
    lines.append("")

    lines.append(
        "## 1. Performance Dataset"
    )
    lines.append("")

    lines.append(
        f"- Historical observations: "
        f"**{performance_stats['observations']}**"
    )

    lines.append(
        f"- Slow-query threshold: "
        f"**{SLOW_QUERY_THRESHOLD_MS:.1f} ms**"
    )

    lines.append(
        f"- Slow-query observations: "
        f"**{performance_stats['slow_queries']}**"
    )

    lines.append("")

    lines.append(
        "## 2. Query Performance"
    )
    lines.append("")

    lines.append(
        "| Metric | Value |"
    )
    lines.append(
        "|---|---:|"
    )

    lines.append(
        f"| Average latency | "
        f"{performance_stats['average']:.3f} ms |"
    )

    lines.append(
        f"| Median latency | "
        f"{performance_stats['median']:.3f} ms |"
    )

    lines.append(
        f"| P95 latency | "
        f"{performance_stats['p95']:.3f} ms |"
    )

    lines.append(
        f"| P99 latency | "
        f"{performance_stats['p99']:.3f} ms |"
    )

    lines.append(
        f"| Minimum latency | "
        f"{performance_stats['minimum']:.3f} ms |"
    )

    lines.append(
        f"| Maximum latency | "
        f"{performance_stats['maximum']:.3f} ms |"
    )

    lines.append("")

    lines.append(
        "## 3. Slow Query Observations"
    )
    lines.append("")

    if top_slow_queries.empty:
        lines.append(
            "No slow-query observations were found."
        )
    else:
        lines.append(
            "| Metric ID | Execution Time (ms) | "
            "Rows Returned |"
        )

        lines.append(
            "|---:|---:|---:|"
        )

        for _, row in top_slow_queries.iterrows():
            lines.append(
                f"| {int(row['metric_id'])} | "
                f"{row['execution_time_ms']:.3f} | "
                f"{int(row['rows_returned'])} |"
            )

    lines.append("")

    lines.append(
        "## 4. Machine Learning Anomaly Detection"
    )
    lines.append("")

    lines.append(
        f"- Detected anomalies: "
        f"**{anomaly_count}**"
    )

    lines.append(
        "- Detection method: "
        "**Isolation Forest**"
    )

    lines.append(
        "- Features used: "
        "**execution time and rows returned**"
    )

    lines.append("")

    lines.append(
        "## 5. Optimization Outcomes"
    )
    lines.append("")

    lines.append(
        "| Outcome | Attempts | Average Improvement |"
    )

    lines.append(
        "|---|---:|---:|"
    )

    lines.append(
        f"| Successful / verified | "
        f"{optimization_stats['successful']} | "
        f"+{optimization_stats['average_successful_improvement']:.2f}% |"
    )

    lines.append(
        f"| Neutral existing-index records | "
        f"{optimization_stats['neutral']} | "
        f"N/A |"
    )

    lines.append(
        f"| Unsuccessful / unstable | "
        f"{optimization_stats['unsuccessful']} | "
        f"See decision breakdown |"
    )

    lines.append(
        f"| Rollbacks | "
        f"{optimization_stats['rollbacks']} | "
        f"Safety outcome |"
    )

    lines.append(
        f"| All recorded attempts | "
        f"{optimization_stats['attempts']} | "
        f"{optimization_stats['overall_average_improvement']:.2f}% |"
    )

    lines.append("")

    lines.append(
        f"- Successful/verified outcome rate: "
        f"**{optimization_stats['success_rate']:.2f}%**"
    )

    lines.append(
        f"- Verified existing indexes: "
        f"**{optimization_stats['verified_existing_indexes']}**"
    )

    lines.append("")

    lines.append(
        "The overall average improvement includes "
        "unstable and rolled-back experiments and "
        "therefore should not be interpreted as the "
        "performance improvement achieved by successful "
        "optimizations. The successful/verified "
        "improvement is reported separately."
    )

    lines.append("")

    lines.append(
        "## 6. Optimization Decision Breakdown"
    )
    lines.append("")

    if decision_breakdown.empty:
        lines.append(
            "No optimization-history records were found."
        )
    else:
        lines.append(
            "| Decision | Attempts | Average Improvement |"
        )

        lines.append(
            "|---|---:|---:|"
        )

        for _, row in decision_breakdown.iterrows():

            decision = str(
                row["decision"]
            )

            attempts = int(
                row["attempts"]
            )

            average_improvement = row[
                "average_improvement"
            ]

            if pd.isna(
                average_improvement
            ):
                improvement_text = "N/A"
            else:
                improvement_text = (
                    f"{average_improvement:.2f}%"
                )

            lines.append(
                f"| {decision} | "
                f"{attempts} | "
                f"{improvement_text} |"
            )

    lines.append("")

    lines.append(
        "## 7. Learning Engine"
    )
    lines.append("")

    lines.append(
        f"- Total optimization attempts: "
        f"**{learning.get('total_attempts', 0)}**"
    )

    lines.append(
        f"- Successful optimizations: "
        f"**{learning.get('successful_optimizations', learning.get('successful', 0))}**"
    )

    lines.append(
        f"- Rollbacks: "
        f"**{learning.get('rollbacks', 0)}**"
    )

    lines.append(
        f"- Success rate: "
        f"**{learning.get('success_rate', 0.0):.2f}%**"
    )

    lines.append(
        f"- Average improvement: "
        f"**{learning.get('average_improvement', 0.0):.2f}%**"
    )

    lines.append(
        f"- Risk level: "
        f"**{learning.get('risk_level', 'UNKNOWN')}**"
    )

    lines.append("")

    lines.append(
        "The learning-engine snapshot is generated "
        "from its current historical-success logic. "
        "The detailed optimization-outcome section "
        "above uses the individual optimization-history "
        "decision categories for experimental reporting."
    )

    lines.append("")

    lines.append(
        "## 8. Resource Health"
    )
    lines.append("")

    lines.append(
        f"- Overall resource status: "
        f"**{resource['status']}**"
    )

    lines.append(
        f"- Connection utilization: "
        f"**{resource['connection_utilization']:.2f}%**"
    )

    lines.append(
        f"- Cache hit ratio: "
        f"**{resource['cache_hit_ratio']:.2f}%**"
    )

    lines.append(
        f"- Rollback rate: "
        f"**{resource['rollback_rate']:.2f}%**"
    )

    lines.append(
        f"- Database size: "
        f"**{resource['database_size_gb']:.4f} GB**"
    )

    lines.append("")

    lines.append(
        "## 9. Cost Analysis"
    )
    lines.append("")

    lines.append(
        f"- Cost status: "
        f"**{cost['status']}**"
    )

    lines.append(
        f"- Estimated monthly compute cost: "
        f"**${cost['compute_cost']:.2f}**"
    )

    lines.append(
        f"- Estimated monthly storage cost: "
        f"**${cost['storage_cost']:.2f}**"
    )

    lines.append(
        f"- Estimated monthly connection cost: "
        f"**${cost['connection_cost']:.2f}**"
    )

    lines.append(
        f"- Estimated monthly total cost: "
        f"**${cost['estimated_monthly_cost']:.2f}**"
    )

    lines.append("")

    lines.append(
        "The cost values are produced by the project's "
        "cloud-agnostic reference pricing model and "
        "should not be interpreted as actual billing "
        "from a specific cloud provider."
    )

    lines.append("")

    lines.append(
        "## 10. Interpretation"
    )
    lines.append("")

    lines.append(
        "The current experimental dataset demonstrates "
        "that the system can collect database "
        "performance observations, identify slow-query "
        "events, detect anomalous behavior, evaluate "
        "resource and cost conditions, and maintain "
        "historical records of optimization outcomes."
    )

    lines.append("")

    lines.append(
        "The optimization results also demonstrate the "
        "role of safety controls. Successful and verified "
        "changes are separated from unstable experiments "
        "and rollbacks, allowing the decision engine to "
        "consider previous outcomes when selecting future "
        "actions."
    )

    lines.append("")

    lines.append(
        "## 11. Reproducibility"
    )
    lines.append("")

    lines.append(
        "This report is generated from the project's "
        "current PostgreSQL performance and "
        "optimization-history tables. Running the "
        "script again after additional workload "
        "collection will refresh the reported values."
    )

    lines.append("")

    return "\n".join(lines)


def main():
    print("=" * 55)
    print(" GENERATING EXPERIMENT RESULTS")
    print("=" * 55)

    performance_df = load_performance_data()

    history_df = load_optimization_history()

    if performance_df.empty:
        print(
            "\nNo performance data available."
        )
        return

    performance_stats = (
        calculate_performance_statistics(
            performance_df
        )
    )

    anomaly_count = detect_anomaly_count(
        performance_df
    )

    optimization_stats = (
        calculate_optimization_statistics(
            history_df
        )
    )

    decision_breakdown = (
        build_decision_breakdown(
            history_df
        )
    )

    learning = get_learning_signal()

    resource = run_resource_optimization()

    cost = run_cost_optimization()

    slow_queries = performance_df[
        performance_df["execution_time_ms"]
        > SLOW_QUERY_THRESHOLD_MS
    ].sort_values(
        "execution_time_ms",
        ascending=False
    ).head(10)

    report = build_report(
        performance_stats=performance_stats,
        anomaly_count=anomaly_count,
        optimization_stats=optimization_stats,
        learning=learning,
        resource=resource,
        cost=cost,
        top_slow_queries=slow_queries,
        decision_breakdown=decision_breakdown
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.write_text(
        report,
        encoding="utf-8"
    )

    print(
        f"\nPerformance observations: "
        f"{performance_stats['observations']}"
    )

    print(
        f"Average latency: "
        f"{performance_stats['average']:.3f} ms"
    )

    print(
        f"P95 latency: "
        f"{performance_stats['p95']:.3f} ms"
    )

    print(
        f"P99 latency: "
        f"{performance_stats['p99']:.3f} ms"
    )

    print(
        f"Slow-query observations: "
        f"{performance_stats['slow_queries']}"
    )

    print(
        f"Detected anomalies: "
        f"{anomaly_count}"
    )

    print(
        f"Optimization attempts: "
        f"{optimization_stats['attempts']}"
    )

    print(
        f"Successful/verified outcomes: "
        f"{optimization_stats['successful']}"
    )

    print(
        f"Successful/verified outcome rate: "
        f"{optimization_stats['success_rate']:.2f}%"
    )

    print(
        f"Average successful/verified improvement: "
        f"{optimization_stats['average_successful_improvement']:.2f}%"
    )

    print(
        f"Overall historical average improvement: "
        f"{optimization_stats['overall_average_improvement']:.2f}%"
    )

    print(
        f"Estimated monthly cost: "
        f"${cost['estimated_monthly_cost']:.2f}"
    )

    print(
        f"\nReport written to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()