import sys
import os

# Allow imports from the project root
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from scripts.decision_engine import (
    load_metrics,
    detect_anomalies,
    analyze_workload,
    make_decision
)

from scripts.workload_prediction import (
    predict_next_execution_time
)

from scripts.autonomous_optimizer import (
    optimize_query
)


# ---------------------------------------------------------
# SYSTEM HEADER
# ---------------------------------------------------------

def print_header():

    print("\n")
    print("=" * 60)
    print(" AI-DRIVEN AUTONOMOUS CLOUD DATABASE OPTIMIZATION SYSTEM")
    print("=" * 60)


# ---------------------------------------------------------
# MAIN AUTONOMOUS PIPELINE
# ---------------------------------------------------------

def run_autonomous_system():

    print_header()

    # -----------------------------------------------------
    # STEP 1 — LOAD DATABASE PERFORMANCE DATA
    # -----------------------------------------------------

    print("\n[1] Loading database performance data...")

    df = load_metrics()

    if len(df) < 10:

        print(
            f"\nNot enough performance data."
        )

        print(
            f"Available records: {len(df)}"
        )

        return


    print(
        f"Loaded {len(df)} performance records."
    )


    # -----------------------------------------------------
    # STEP 2 — AI ANOMALY DETECTION
    # -----------------------------------------------------

    print(
        "\n[2] Running AI anomaly detection..."
    )

    df["is_anomaly"] = detect_anomalies(df)

    anomaly_count = int(
        df["is_anomaly"].sum()
    )

    print(
        f"ML anomalies detected: {anomaly_count}"
    )


    # -----------------------------------------------------
    # STEP 3 — WORKLOAD ANALYSIS
    # -----------------------------------------------------

    print(
        "\n[3] Analyzing workload..."
    )

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


    # -----------------------------------------------------
    # STEP 4 — WORKLOAD PREDICTION
    # -----------------------------------------------------

    print(
        "\n[4] Predicting future workload performance..."
    )

    predicted_latency = (
        predict_next_execution_time(df)
    )

    if predicted_latency is not None:

        print(
            f"Predicted next execution time: "
            f"{predicted_latency:.3f} ms"
        )

    else:

        print(
            "Prediction unavailable."
        )


    # -----------------------------------------------------
    # STEP 5 — AUTONOMOUS DECISION
    # -----------------------------------------------------

    print(
        "\n[5] Running autonomous decision engine..."
    )

    decision = make_decision(
        analysis,
        predicted_latency
    )


    print(
        "\nDecision selected:"
    )

    print(
        f"Action: {decision['action']}"
    )


    # -----------------------------------------------------
    # STEP 6 — EXECUTE OPTIMIZATION
    # -----------------------------------------------------

    if decision["action"] == "OPTIMIZE_INDEX":

        print(
            "\n[6] Autonomous optimization triggered."
        )

        if (
            decision["metric_id"] is None
            or decision["query_text"] is None
            or decision["table"] is None
            or decision["column"] is None
        ):

            print(
                "Optimization target is incomplete."
            )

            print(
                "Optimization cancelled for safety."
            )

            return


        result = optimize_query(
            metric_id=decision["metric_id"],
            query_text=decision["query_text"],
            table_name=decision["table"],
            column_name=decision["column"]
        )


        # -------------------------------------------------
        # STEP 7 — DISPLAY VERIFICATION RESULT
        # -------------------------------------------------

        print(
            "\n[7] Optimization verification complete."
        )

        print(
            f"Baseline: "
            f"{result['baseline_time_ms']:.3f} ms"
        )

        print(
            f"Optimized: "
            f"{result['optimized_time_ms']:.3f} ms"
        )

        print(
            f"Improvement: "
            f"{result['improvement_percent']:.2f}%"
        )

        print(
            f"Decision: "
            f"{result['decision']}"
        )


    # -----------------------------------------------------
    # STEP 6B — WORKLOAD ANALYSIS
    # -----------------------------------------------------

    elif decision["action"] == "ANALYZE_WORKLOAD":

        print(
            "\n[6] Additional workload analysis required."
        )

        print(
            "No automatic database modification performed."
        )


    # -----------------------------------------------------
    # STEP 6C — MONITORING
    # -----------------------------------------------------

    elif decision["action"] == "MONITOR":

        print(
            "\n[6] System workload is within normal limits."
        )

        print(
            "Continuing monitoring."
        )


    # -----------------------------------------------------
    # FINAL STATUS
    # -----------------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        " FINAL SYSTEM STATUS"
    )

    print(
        "=" * 60
    )

    print(
        f"Action: {decision['action']}"
    )

    print(
        f"Learning risk: "
        f"{decision['learning_risk']}"
    )

    if decision["table"] is not None:

        print(
            f"Target: "
            f"{decision['table']}."
            f"{decision['column']}"
        )

    print(
        "\nAutonomous optimization cycle completed."
    )

    print(
        "=" * 60
    )


# ---------------------------------------------------------
# PROGRAM ENTRY POINT
# ---------------------------------------------------------

if __name__ == "__main__":

    run_autonomous_system()