import json

import pandas as pd
from sqlalchemy import text

from scripts import decision_engine
from scripts.cost_optimizer import run_cost_optimization
from scripts.generate_results import (
    calculate_optimization_statistics,
    calculate_performance_statistics,
)
from scripts.learning_engine import get_learning_signal
from scripts.resource_optimizer import run_resource_optimization
from scripts.workload_prediction import predict_next_execution_time


PERFORMANCE_QUERY = """
    SELECT
        metric_id,
        query_text,
        execution_time_ms,
        rows_returned,
        recorded_at
    FROM query_performance
    ORDER BY recorded_at DESC
    LIMIT :limit;
"""

OPTIMIZATION_QUERY = """
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
    ORDER BY created_at DESC
    LIMIT :limit;
"""


def _records(frame):
    if frame.empty:
        return []
    return json.loads(
        frame.to_json(
            orient="records",
            date_format="iso",
        )
    )


def load_performance_frame(limit=5000):
    engine = decision_engine.get_engine()
    try:
        frame = pd.read_sql_query(
            text(PERFORMANCE_QUERY),
            engine,
            params={"limit": limit},
        )
    finally:
        engine.dispose()

    return frame.sort_values("recorded_at").reset_index(drop=True)


def load_optimization_frame(limit=5000):
    engine = decision_engine.get_engine()
    try:
        frame = pd.read_sql_query(
            text(OPTIMIZATION_QUERY),
            engine,
            params={"limit": limit},
        )
    finally:
        engine.dispose()

    return frame.sort_values("created_at").reset_index(drop=True)


def get_performance(limit=500, slow_only=False, search=None):
    frame = load_performance_frame(limit)
    if slow_only:
        frame = frame[
            frame["execution_time_ms"]
            > decision_engine.SLOW_QUERY_THRESHOLD_MS
        ]
    if search:
        frame = frame[
            frame["query_text"].str.contains(
                search,
                case=False,
                regex=False,
                na=False,
            )
        ]

    return {
        "threshold_ms": decision_engine.SLOW_QUERY_THRESHOLD_MS,
        "records": _records(frame),
    }


def get_performance_summary():
    frame = load_performance_frame()
    if frame.empty:
        return {
            "observations": 0,
            "slow_queries": 0,
            "average": None,
            "median": None,
            "p95": None,
            "p99": None,
            "minimum": None,
            "maximum": None,
        }

    summary = calculate_performance_statistics(frame)
    return {
        "observations": summary["observations"],
        "slow_queries": summary["slow_queries"],
        "average": summary["average"],
        "median": summary["median"],
        "p95": summary["p95"],
        "p99": summary["p99"],
        "minimum": summary["minimum"],
        "maximum": summary["maximum"],
    }


def get_anomalies():
    frame = load_performance_frame()
    if frame.empty:
        return {"total": 0, "records": []}

    classified = decision_engine.detect_anomalies(frame)
    anomalies = classified[classified["anomaly"] == -1]
    return {
        "total": len(anomalies),
        "records": _records(classified),
    }


def get_prediction():
    frame = load_performance_frame()
    if len(frame) < 10:
        return {
            "status": "INSUFFICIENT_DATA",
            "observations": len(frame),
            "average_latency_ms": (
                float(frame["execution_time_ms"].mean())
                if not frame.empty
                else None
            ),
            "maximum_latency_ms": (
                float(frame["execution_time_ms"].max())
                if not frame.empty
                else None
            ),
            "predicted_latency_ms": None,
            "interpretation": (
                "At least 10 observations are required for prediction."
            ),
        }

    prediction = predict_next_execution_time(frame)
    average = float(frame["execution_time_ms"].mean())
    maximum = float(frame["execution_time_ms"].max())
    predicted = float(prediction) if prediction is not None else None
    return {
        "status": "READY" if predicted is not None else "UNAVAILABLE",
        "observations": len(frame),
        "average_latency_ms": average,
        "maximum_latency_ms": maximum,
        "predicted_latency_ms": predicted,
        "interpretation": (
            "Potential degradation compared with historical average."
            if predicted is not None and predicted > average
            else "Expected performance within the historical average."
            if predicted is not None
            else "Prediction is unavailable."
        ),
    }


def get_optimization_history(limit=500):
    frame = load_optimization_frame(limit)
    return {"records": _records(frame)}


def get_optimization_summary():
    frame = load_optimization_frame()
    summary = calculate_optimization_statistics(frame)
    summary["decisions"] = (
        frame["decision"].value_counts().to_dict()
        if not frame.empty
        else {}
    )
    return summary


def get_resources():
    return run_resource_optimization()


def get_costs():
    return run_cost_optimization()


def get_learning():
    return get_learning_signal()


def get_dashboard():
    performance = load_performance_frame()
    history = load_optimization_frame()
    performance_summary = (
        calculate_performance_statistics(performance)
        if not performance.empty
        else get_performance_summary()
    )
    anomaly_data = (
        decision_engine.detect_anomalies(performance)
        if not performance.empty
        else performance.assign(anomaly=pd.Series(dtype="int64"))
    )
    anomaly_count = int((anomaly_data.get("anomaly") == -1).sum())
    optimization_summary = calculate_optimization_statistics(history)
    decision_counts = (
        history["decision"].value_counts().to_dict()
        if not history.empty
        else {}
    )
    prediction = get_prediction_from_frame(performance)

    return {
        "performance": {
            "summary": performance_summary,
            "records": _records(performance.tail(500)),
            "threshold_ms": decision_engine.SLOW_QUERY_THRESHOLD_MS,
        },
        "anomalies": {
            "total": anomaly_count,
            "records": _records(anomaly_data.tail(500)),
        },
        "prediction": prediction,
        "optimization": {
            "summary": {
                **optimization_summary,
                "decisions": decision_counts,
            },
            "history": _records(history.tail(100)),
        },
        "resources": get_resources(),
        "costs": get_costs(),
        "learning": get_learning(),
        "latest_recorded_decision": (
            str(history.iloc[-1]["decision"])
            if not history.empty
            else None
        ),
        "decision_analysis_status": "NOT_ANALYZED",
    }


def get_prediction_from_frame(frame):
    if len(frame) < 10:
        return {
            "status": "INSUFFICIENT_DATA",
            "observations": len(frame),
            "average_latency_ms": (
                float(frame["execution_time_ms"].mean())
                if not frame.empty
                else None
            ),
            "maximum_latency_ms": (
                float(frame["execution_time_ms"].max())
                if not frame.empty
                else None
            ),
            "predicted_latency_ms": None,
            "interpretation": (
                "At least 10 observations are required for prediction."
            ),
        }

    prediction = predict_next_execution_time(frame)
    average = float(frame["execution_time_ms"].mean())
    predicted = float(prediction) if prediction is not None else None
    return {
        "status": "READY" if predicted is not None else "UNAVAILABLE",
        "observations": len(frame),
        "average_latency_ms": average,
        "maximum_latency_ms": float(frame["execution_time_ms"].max()),
        "predicted_latency_ms": predicted,
        "interpretation": (
            "Potential degradation compared with historical average."
            if predicted is not None and predicted > average
            else "Expected performance within the historical average."
            if predicted is not None
            else "Prediction is unavailable."
        ),
    }


def analyze_optimization(metric_id=None):
    frame = load_performance_frame()
    if frame.empty:
        return {
            "status": "NO_DATA",
            "reason": "No performance observations are available.",
            "decision": None,
        }

    selected = frame
    if metric_id is not None:
        selected = frame[frame["metric_id"] == metric_id]
        if selected.empty:
            return {
                "status": "NOT_FOUND",
                "reason": "The requested performance metric was not found.",
                "decision": None,
            }

    analysis = decision_engine.analyze_workload(selected)
    prediction = predict_next_execution_time(frame)
    decision = decision_engine.make_decision(
        analysis,
        predicted_latency=prediction,
    )
    return {
        "status": "ANALYZED",
        "metric_id": analysis["latest_metric_id"],
        "reason": _decision_reason(analysis, decision),
        "analysis": analysis,
        "decision": decision,
    }


def execute_optimization(metric_id, expected_action):
    analysis_result = analyze_optimization(metric_id)
    if analysis_result["status"] != "ANALYZED":
        return {**analysis_result, "execution": None}

    decision = analysis_result["decision"]
    if decision["action"] != expected_action:
        return {
            "status": "STALE_PREVIEW",
            "reason": (
                "The current decision differs from the preview. "
                "Analyze again before confirming execution."
            ),
            "decision": decision,
            "execution": None,
        }

    executable_actions = {
        "OPTIMIZE_INDEX",
        "OPTIMIZE_COMPOSITE_INDEX",
        "VERIFY_EXISTING_COMPOSITE_INDEX",
    }
    if decision["action"] not in executable_actions:
        return {
            **analysis_result,
            "status": "NO_EXECUTABLE_ACTION",
            "execution": None,
        }

    from src.main import execute_decision

    execution = execute_decision(decision, analysis_result["analysis"])
    return {
        **analysis_result,
        "status": "EXECUTED",
        "execution": execution,
        "final_status": (
            execution.get("decision", "UNKNOWN")
            if isinstance(execution, dict)
            else "UNKNOWN"
        ),
    }


def _decision_reason(analysis, decision):
    action = decision["action"]
    if action == "RESOURCE_PROTECTION":
        return "Optimization is blocked by critical resource pressure."
    if action == "COST_PROTECTION":
        return "Optimization is blocked by the cost-protection policy."
    if analysis["latest_latency"] <= decision_engine.SLOW_QUERY_THRESHOLD_MS:
        return "Latest observed latency is within the slow-query threshold."
    if decision.get("plan_recommendation"):
        return str(decision["plan_recommendation"])
    if decision.get("plan_status"):
        return str(decision["plan_status"])
    return "A slow query was observed; no safe automatic action was selected."