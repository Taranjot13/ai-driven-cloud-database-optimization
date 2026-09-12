from scripts.monitor_database import monitor_database
from scripts.detect_slow_queries import detect_slow_queries
from scripts.workload_prediction import run_prediction
from scripts.decision_engine import (
    load_metrics,
    detect_anomalies,
    analyze_workload,
    make_decision
)
from scripts.autonomous_optimizer import (
    optimize_index
)
from scripts.composite_index_optimizer import (
    optimize_composite_index
)
from scripts.learning_engine import (
    get_learning_signal
)


def print_learning_status():
    learning = get_learning_signal()

    print("\n===== LEARNING STATUS =====")
    print(
        f"Optimization attempts: "
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
        f"Historical success rate: "
        f"{learning['success_rate']:.2f}%"
    )
    print(
        f"Average improvement: "
        f"{learning['average_improvement']:.2f}%"
    )
    print(
        f"Learning risk: "
        f"{learning['risk_level']}"
    )

    return learning


def main():

    print("\n========================================")
    print(" AI-DRIVEN CLOUD DATABASE OPTIMIZATION")
    print("========================================")

    # =========================================================
    # 1. DATABASE MONITORING
    # =========================================================

    print("\n[1] DATABASE MONITORING")

    monitor_database()

    # =========================================================
    # 2. SLOW QUERY DETECTION
    # =========================================================

    print("\n[2] SLOW QUERY DETECTION")

    detect_slow_queries()

    # =========================================================
    # 3. WORKLOAD PREDICTION
    # =========================================================

    print("\n[3] WORKLOAD PREDICTION")

    predicted_latency = run_prediction()

    # =========================================================
    # 4. LOAD PERFORMANCE DATA
    # =========================================================

    df = load_metrics()

    if len(df) < 10:

        print(
            "\nNot enough performance data "
            "for autonomous optimization."
        )

        return

    # =========================================================
    # 5. AI ANOMALY DETECTION
    # =========================================================

    print("\n[4] AI ANOMALY DETECTION")

    df["is_anomaly"] = detect_anomalies(df)

    anomaly_count = int(
        df["is_anomaly"].sum()
    )

    print(
        f"Anomalies detected: "
        f"{anomaly_count}"
    )

    # =========================================================
    # 6. WORKLOAD ANALYSIS
    # =========================================================

    print("\n[5] WORKLOAD ANALYSIS")

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
        f"Slow queries: "
        f"{len(analysis['slow_queries'])}"
    )

    # =========================================================
    # 7. AUTONOMOUS DECISION ENGINE
    # =========================================================

    print("\n[6] AUTONOMOUS DECISION ENGINE")

    decision = make_decision(
        analysis,
        predicted_latency
    )

    print(
        f"\nSelected action: "
        f"{decision['action']}"
    )

    # =========================================================
    # 8. EXECUTE DECISION
    # =========================================================

    action = decision["action"]

    # ---------------------------------------------------------
    # NORMAL MONITORING
    # ---------------------------------------------------------

    if action == "MONITOR":

        print(
            "\n[7] MONITORING MODE"
        )

        print(
            "No database modification required."
        )

    # ---------------------------------------------------------
    # STANDARD INDEX OPTIMIZATION
    # ---------------------------------------------------------

    elif action == "OPTIMIZE_INDEX":

        print(
            "\n[7] AUTONOMOUS INDEX OPTIMIZATION"
        )

        result = optimize_index(
            metric_id=decision["metric_id"],
            query_text=decision["query_text"],
            table_name=decision["table"],
            column_name=decision["column"]
        )

        print(
            "\nOptimization result:"
        )

        print(
            f"Decision: "
            f"{result.get('decision')}"
        )

        if result.get("baseline_time_ms") is not None:
            print(
                f"Baseline: "
                f"{result['baseline_time_ms']:.3f} ms"
            )

        if result.get("optimized_time_ms") is not None:
            print(
                f"Optimized: "
                f"{result['optimized_time_ms']:.3f} ms"
            )

        if result.get("improvement_percent") is not None:
            print(
                f"Improvement: "
                f"{result['improvement_percent']:.2f}%"
            )

    # ---------------------------------------------------------
    # COMPOSITE INDEX OPTIMIZATION
    # ---------------------------------------------------------

    elif action == "OPTIMIZE_COMPOSITE_INDEX":

        print(
            "\n[7] AUTONOMOUS COMPOSITE INDEX OPTIMIZATION"
        )

        result = optimize_composite_index(
            metric_id=decision["metric_id"],
            query_text=decision["query_text"],
            table_name=decision["table"],
            filter_column=decision["filter_column"],
            order_column=decision["order_column"],
            direction=decision["order_direction"]
        )

        print(
            "\nComposite optimization result:"
        )

        print(
            f"Decision: "
            f"{result.get('decision')}"
        )

        if result.get("baseline_time_ms") is not None:
            print(
                f"Baseline median: "
                f"{result['baseline_time_ms']:.3f} ms"
            )

        if result.get("optimized_time_ms") is not None:
            print(
                f"Optimized median: "
                f"{result['optimized_time_ms']:.3f} ms"
            )

        if result.get("improvement_percent") is not None:
            print(
                f"Observed improvement: "
                f"{result['improvement_percent']:.2f}%"
            )

        if result.get("decision") == "EXISTING_INDEX":

            print(
                "\nExisting composite index detected."
            )

            print(
                f"Index preserved: "
                f"{result.get('index_name')}"
            )

            print(
                "No new index was created."
            )

            print(
                "No performance improvement was "
                "claimed because no new comparison "
                "was performed."
            )

    # ---------------------------------------------------------
    # EXISTING COMPOSITE INDEX VERIFICATION
    # ---------------------------------------------------------

    elif action == "VERIFY_EXISTING_COMPOSITE_INDEX":

        print(
            "\n[7] EXISTING COMPOSITE INDEX VERIFICATION"
        )

        print(
            "The decision engine detected that a "
            "matching composite index already exists."
        )

        print(
            "\nTarget:"
        )

        print(
            f"Table: "
            f"{decision['table']}"
        )

        print(
            f"Filter column: "
            f"{decision['filter_column']}"
        )

        print(
            f"Order column: "
            f"{decision['order_column']}"
        )

        print(
            f"Order direction: "
            f"{decision['order_direction']}"
        )

        print(
            "\nRunning measured verification..."
        )

        result = optimize_composite_index(
            metric_id=decision["metric_id"],
            query_text=decision["query_text"],
            table_name=decision["table"],
            filter_column=decision["filter_column"],
            order_column=decision["order_column"],
            direction=decision["order_direction"]
        )

        print(
            "\n===== EXISTING INDEX VERIFICATION RESULT ====="
        )

        print(
            f"Decision: "
            f"{result.get('decision')}"
        )

        if result.get("index_name"):

            print(
                f"Index: "
                f"{result['index_name']}"
            )

        if result.get("baseline_time_ms") is not None:

            print(
                f"Measured median: "
                f"{result['baseline_time_ms']:.3f} ms"
            )

        if result.get("optimized_time_ms") is not None:

            print(
                f"Optimized median: "
                f"{result['optimized_time_ms']:.3f} ms"
            )

        if result.get("improvement_percent") is not None:

            print(
                f"Observed improvement: "
                f"{result['improvement_percent']:.2f}%"
            )

        if result.get("decision") == "EXISTING_INDEX":

            print(
                "\nExisting index preserved."
            )

            print(
                "No new index was created."
            )

        elif result.get("decision") == "EXISTING INDEX VERIFIED":

            print(
                "\nExisting composite index verified."
            )

            print(
                "The index produced a stable "
                "measured performance result."
            )

        elif result.get("decision") == "EXISTING INDEX NOT VERIFIED":

            print(
                "\nExisting composite index could "
                "not be positively verified."
            )

            print(
                "The system did not create a replacement "
                "index automatically."
            )

        elif result.get("decision") == "MEASUREMENT UNSTABLE":

            print(
                "\nVerification measurement was unstable."
            )

            print(
                "The existing index was preserved "
                "because the system could not establish "
                "a reliable performance conclusion."
            )

    # ---------------------------------------------------------
    # WORKLOAD ANALYSIS
    # ---------------------------------------------------------

    elif action == "ANALYZE_WORKLOAD":

        print(
            "\n[7] ADDITIONAL WORKLOAD ANALYSIS"
        )

        print(
            "No automatic database modification performed."
        )

        print(
            f"Plan status: "
            f"{decision['plan_status']}"
        )

    # ---------------------------------------------------------
    # UNKNOWN ACTION
    # ---------------------------------------------------------

    else:

        print(
            "\n[7] UNKNOWN DECISION"
        )

        print(
            f"Action returned by decision engine: "
            f"{action}"
        )

        print(
            "No database modification performed."
        )

    # =========================================================
    # 9. LEARNING STATUS
    # =========================================================

    print_learning_status()

    # =========================================================
    # 10. FINAL SYSTEM STATUS
    # =========================================================

    print(
        "\n========================================"
    )

    print(
        " FINAL SYSTEM STATUS"
    )

    print(
        "========================================"
    )

    print(
        f"Action: "
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

    print(
        f"Plan status: "
        f"{decision['plan_status']}"
    )

    if decision["table"] is not None:

        if decision["order_column"] is not None:

            print(
                "Target: "
                f"{decision['table']}."
                f"{decision['filter_column']}, "
                f"{decision['order_column']} "
                f"{decision['order_direction']}"
            )

        else:

            print(
                "Target: "
                f"{decision['table']}."
                f"{decision['column']}"
            )

    print(
        "\nAutonomous optimization cycle completed."
    )


if __name__ == "__main__":
    main()
