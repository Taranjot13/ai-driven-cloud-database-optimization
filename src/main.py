from scripts.monitor_database import monitor_database
from scripts.detect_slow_queries import detect_slow_queries
from scripts.workload_prediction import run_prediction
from scripts.anomaly_detection import load_metrics as load_anomaly_metrics
from scripts.decision_engine import (
    load_metrics,
    detect_anomalies,
    analyze_workload,
    make_decision
)
from scripts.autonomous_optimizer import optimize_query
from scripts.composite_index_optimizer import (
    optimize_composite_index,
    verify_existing_index
)
from scripts.learning_engine import get_learning_signal


SLOW_QUERY_THRESHOLD_MS = 5.0


def print_learning_status():
    print("\n===== LEARNING STATUS =====")

    try:
        learning = get_learning_signal()

        print(
            f"Optimization attempts: "
            f"{learning.get('total_attempts', 0)}"
        )

        print(
            f"Successful optimizations: "
            f"{learning.get('successful_optimizations',
                            learning.get('successful', 0))}"
        )

        print(
            f"Rollbacks: "
            f"{learning.get('rollbacks', 0)}"
        )

        print(
            f"Historical success rate: "
            f"{learning.get('success_rate', 0.0):.2f}%"
        )

        print(
            f"Average improvement: "
            f"{learning.get('average_improvement', 0.0):.2f}%"
        )

        print(
            f"Learning risk: "
            f"{learning.get('risk_level', 'UNKNOWN')}"
        )

    except Exception as error:
        print(
            f"Learning status unavailable: {error}"
        )


def print_resource_status(decision):
    print("\n===== RESOURCE STATUS =====")

    print(
        f"Resource health: "
        f"{decision.get('resource_status', 'UNKNOWN')}"
    )

    metrics = decision.get(
        "resource_metrics",
        {}
    )

    print(
        f"Connection utilization: "
        f"{metrics.get('connection_utilization', 0.0):.2f}%"
    )

    print(
        f"Cache hit ratio: "
        f"{metrics.get('cache_hit_ratio', 0.0):.2f}%"
    )

    print(
        f"Rollback rate: "
        f"{metrics.get('rollback_rate', 0.0):.2f}%"
    )

    print(
        f"Database size: "
        f"{metrics.get('database_size_gb', 0.0):.4f} GB"
    )

    recommendations = decision.get(
        "resource_recommendations",
        []
    )

    if recommendations:
        print("\nResource recommendations:")

        for recommendation in recommendations:
            print(f"- {recommendation}")


def print_cost_status(decision):
    print("\n===== COST STATUS =====")

    cost_status = decision.get(
        "cost_status",
        "UNKNOWN"
    )

    print(
        f"Cost health: "
        f"{cost_status}"
    )

    cost_metrics = decision.get(
        "cost_metrics",
        {}
    )

    print(
        f"Estimated monthly cost: "
        f"${cost_metrics.get('estimated_monthly_cost', 0.0):.2f}"
    )

    print(
        f"Estimated compute cost: "
        f"${cost_metrics.get('compute_cost', 0.0):.2f}"
    )

    print(
        f"Estimated storage cost: "
        f"${cost_metrics.get('storage_cost', 0.0):.2f}"
    )

    print(
        f"Estimated connection cost: "
        f"${cost_metrics.get('connection_cost', 0.0):.2f}"
    )

    recommendations = decision.get(
        "cost_recommendations",
        []
    )

    if recommendations:
        print("\nCost recommendations:")

        for recommendation in recommendations:
            print(f"- {recommendation}")


def execute_decision(decision, analysis):
    action = decision.get(
        "action",
        "MONITOR"
    )

    target = decision.get(
        "target",
        {}
    )

    metric_id = analysis.get(
        "latest_metric_id"
    )

    query_text = analysis.get(
        "latest_query"
    )

    table_name = target.get(
        "table_name"
    )

    column_name = target.get(
        "column_name"
    )

    order_column = target.get(
        "order_column"
    )

    order_direction = target.get(
        "order_direction"
    )

    print("\n===== DECISION EXECUTION =====")

    print(
        f"Selected action: {action}"
    )

    if action == "MONITOR":

        print(
            "No database modification performed."
        )

        print(
            "The system will continue monitoring "
            "the workload."
        )

        return None

    if action == "ANALYZE_WORKLOAD":

        print(
            "No automatic database modification performed."
        )

        print(
            "The system will continue monitoring "
            "the workload before making a modification."
        )

        return None

    if action == "RESOURCE_PROTECTION":

        print(
            "Optimization blocked because of "
            "critical resource pressure."
        )

        return None

    if action == "COST_PROTECTION":

        print(
            "Optimization blocked because of "
            "high cost risk."
        )

        return None

    if action == "OPTIMIZE_INDEX":

        if not all(
            [
                metric_id,
                query_text,
                table_name,
                column_name
            ]
        ):
            print(
                "Insufficient information for "
                "single-column optimization."
            )

            return None

        print(
            "\nStarting autonomous index optimization..."
        )

        return optimize_query(
            metric_id=metric_id,
            query_text=query_text,
            table_name=table_name,
            column_name=column_name
        )

    if action == "OPTIMIZE_COMPOSITE_INDEX":

        if not all(
            [
                metric_id,
                query_text,
                table_name,
                column_name,
                order_column
            ]
        ):
            print(
                "Insufficient information for "
                "composite-index optimization."
            )

            return None

        print(
            "\nStarting autonomous composite-index optimization..."
        )

        return optimize_composite_index(
            metric_id=metric_id,
            query_text=query_text,
            table_name=table_name,
            filter_column=column_name,
            order_column=order_column,
            order_direction=order_direction
        )

    if action == "VERIFY_EXISTING_COMPOSITE_INDEX":

        if not all(
            [
                metric_id,
                query_text,
                table_name,
                column_name,
                order_column
            ]
        ):
            print(
                "Insufficient information for "
                "composite-index verification."
            )

            return None

        print(
            "\nStarting existing composite-index verification..."
        )

        return verify_existing_index(
            metric_id=metric_id,
            query_text=query_text,
            table_name=table_name,
            filter_column=column_name,
            order_column=order_column,
            order_direction=order_direction
        )

    print(
        f"Unknown action: {action}"
    )

    return None


def main():
    print("\n========================================")
    print(" AI-DRIVEN CLOUD DATABASE OPTIMIZATION")
    print("========================================")

    # --------------------------------------------------
    # 1. DATABASE MONITORING
    # --------------------------------------------------

    print("\n[1] DATABASE MONITORING")

    monitoring_result = monitor_database()

    if monitoring_result is None:
        print(
            "Database monitoring did not return a result."
        )

    # --------------------------------------------------
    # 2. SLOW QUERY DETECTION
    # --------------------------------------------------

    print("\n[2] SLOW QUERY DETECTION")

    slow_queries = detect_slow_queries()

    if slow_queries is None:
        slow_queries = []

    # --------------------------------------------------
    # 3. WORKLOAD PREDICTION
    # --------------------------------------------------

    print("\n[3] WORKLOAD PREDICTION")

    prediction = run_prediction()

    # --------------------------------------------------
    # 4. LOAD PERFORMANCE DATA
    # --------------------------------------------------

    print("\n[4] LOADING PERFORMANCE DATA")

    df = load_metrics()

    print(
        f"Historical observations: {len(df)}"
    )

    if df.empty:
        print(
            "\nNo performance data available."
        )

        print(
            "Autonomous optimization cycle cannot continue."
        )

        return

    # --------------------------------------------------
    # 5. AI ANOMALY DETECTION
    # --------------------------------------------------

    print("\n[5] AI ANOMALY DETECTION")

    anomaly_df = detect_anomalies(df)

    if "status" in anomaly_df.columns:

        anomaly_count = int(
            (
                anomaly_df["status"]
                == "Anomaly"
            ).sum()
        )

    elif "anomaly" in anomaly_df.columns:

        anomaly_count = int(
            (
                anomaly_df["anomaly"]
                == -1
            ).sum()
        )

    else:

        anomaly_count = 0

    print(
        f"Anomalies detected: {anomaly_count}"
    )

    if anomaly_count > 0:

        anomalous_records = anomaly_df[
            anomaly_df["status"]
            == "Anomaly"
        ]

        print(
            "\nDetected anomalous performance records:"
        )

        columns = [
            "metric_id",
            "execution_time_ms",
            "rows_returned",
            "status"
        ]

        available_columns = [
            column
            for column in columns
            if column in anomalous_records.columns
        ]

        if available_columns:

            print(
                anomalous_records[
                    available_columns
                ].to_string(index=False)
            )

    # --------------------------------------------------
    # 6. WORKLOAD ANALYSIS
    # --------------------------------------------------

    print("\n[6] WORKLOAD ANALYSIS")

    analysis = analyze_workload(df)

    print(
        f"Average latency: "
        f"{analysis['average_latency']:.3f} ms"
    )

    print(
        f"Latest latency: "
        f"{analysis['latest_latency']:.3f} ms"
    )

    print(
        f"Maximum latency: "
        f"{analysis['maximum_latency']:.3f} ms"
    )

    print(
        f"Slow queries: "
        f"{analysis['slow_queries']}"
    )

    # --------------------------------------------------
    # 7. AUTONOMOUS DECISION ENGINE
    # --------------------------------------------------

    print("\n[7] AUTONOMOUS DECISION ENGINE")

    decision = make_decision(
        analysis=analysis,
        predicted_latency=prediction
    )

    # --------------------------------------------------
    # RESOURCE STATUS
    # --------------------------------------------------

    print_resource_status(
        decision
    )

    # --------------------------------------------------
    # COST STATUS
    # --------------------------------------------------

    print_cost_status(
        decision
    )

    # --------------------------------------------------
    # 8. DECISION EXECUTION
    # --------------------------------------------------

    print("\n[8] DECISION EXECUTION")

    optimization_result = execute_decision(
        decision=decision,
        analysis=analysis
    )

    if optimization_result is not None:

        print(
            "\nOptimization result:"
        )

        if isinstance(
            optimization_result,
            dict
        ):

            for key, value in (
                optimization_result.items()
            ):

                print(
                    f"{key}: {value}"
                )

        else:

            print(
                optimization_result
            )

    # --------------------------------------------------
    # 9. LEARNING STATUS
    # --------------------------------------------------

    print_learning_status()

    # --------------------------------------------------
    # 10. FINAL SYSTEM STATUS
    # --------------------------------------------------

    print("\n========================================")
    print(" FINAL SYSTEM STATUS")
    print("========================================")

    print(
        f"Action: "
        f"{decision.get('action', 'UNKNOWN')}"
    )

    print(
        f"Learning risk: "
        f"{decision.get('learning_risk', 'UNKNOWN')}"
    )

    print(
        f"Learning policy: "
        f"{decision.get('learning_policy', 'UNKNOWN')}"
    )

    print(
        f"Plan status: "
        f"{decision.get('plan_status')}"
    )

    print(
        f"Resource status: "
        f"{decision.get('resource_status', 'UNKNOWN')}"
    )

    print(
        f"Cost status: "
        f"{decision.get('cost_status', 'UNKNOWN')}"
    )

    cost_metrics = decision.get(
        "cost_metrics",
        {}
    )

    print(
        f"Estimated monthly cost: "
        f"${cost_metrics.get('estimated_monthly_cost', 0.0):.2f}"
    )

    print(
        "\nAutonomous optimization cycle completed."
    )


if __name__ == "__main__":
    main()