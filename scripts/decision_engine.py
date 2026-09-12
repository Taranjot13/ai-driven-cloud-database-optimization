import re

import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import IsolationForest

from scripts.query_plan_analyzer import analyze_query_plan


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "cloud_optimizer",
    "user": "postgres",
    "password": "123456t"
}

SLOW_QUERY_THRESHOLD_MS = 5.0


def get_engine():
    connection_url = (
        f"postgresql+psycopg2://"
        f"{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}"
        f"/{DB_CONFIG['database']}"
    )
    return create_engine(connection_url)


def load_metrics():
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

    df = pd.read_sql_query(query, engine)
    engine.dispose()

    return df


def detect_anomalies(df):
    result = df.copy()

    if len(result) < 10:
        result["is_anomaly"] = False
        return result["is_anomaly"]

    features = result[
        ["execution_time_ms", "rows_returned"]
    ]

    model = IsolationForest(
        contamination=0.10,
        random_state=42
    )

    predictions = model.fit_predict(features)

    result["is_anomaly"] = predictions == -1

    return result["is_anomaly"]


def analyze_workload(df):
    average_latency = df["execution_time_ms"].mean()
    latest_latency = df.iloc[-1]["execution_time_ms"]

    slow_queries = df[
        df["execution_time_ms"] > SLOW_QUERY_THRESHOLD_MS
    ].copy()

    return {
        "average_latency": average_latency,
        "latest_latency": latest_latency,
        "slow_queries": slow_queries
    }


def extract_query_target(query_text):
    if not query_text:
        return None

    table_match = re.search(
        r"\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        r"(?:\s+[a-zA-Z_][a-zA-Z0-9_]*)?",
        query_text,
        re.IGNORECASE
    )

    column_match = re.search(
        r"\bWHERE\s+"
        r"(?:[a-zA-Z_][a-zA-Z0-9_]*\.)?"
        r"([a-zA-Z_][a-zA-Z0-9_]*)\s*=",
        query_text,
        re.IGNORECASE
    )

    if not table_match or not column_match:
        return None

    return {
        "table": table_match.group(1),
        "column": column_match.group(1)
    }


def extract_composite_index_target(query_text):
    """
    Supports both:

        WHERE customer_id = ...
        ORDER BY order_date DESC

    and:

        WHERE o.customer_id = ...
        ORDER BY o.order_date DESC
    """

    if not query_text:
        return None

    table_match = re.search(
        r"\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        r"(?:\s+([a-zA-Z_][a-zA-Z0-9_]*))?",
        query_text,
        re.IGNORECASE
    )

    filter_match = re.search(
        r"\bWHERE\s+"
        r"(?:[a-zA-Z_][a-zA-Z0-9_]*\.)?"
        r"([a-zA-Z_][a-zA-Z0-9_]*)\s*=",
        query_text,
        re.IGNORECASE
    )

    order_match = re.search(
        r"\bORDER\s+BY\s+"
        r"(?:[a-zA-Z_][a-zA-Z0-9_]*\.)?"
        r"([a-zA-Z_][a-zA-Z0-9_]*)"
        r"(?:\s+(ASC|DESC))?",
        query_text,
        re.IGNORECASE
    )

    if not table_match or not filter_match or not order_match:
        return None

    order_direction = order_match.group(2)

    if order_direction is None:
        order_direction = "ASC"

    return {
        "table": table_match.group(1),
        "filter_column": filter_match.group(1),
        "order_column": order_match.group(1),
        "order_direction": order_direction.upper()
    }


def calculate_learning_risk():
    engine = get_engine()

    query = """
        SELECT
            optimization_type,
            decision,
            improvement_percent
        FROM optimization_history
        ORDER BY created_at;
    """

    history = pd.read_sql_query(query, engine)
    engine.dispose()

    if history.empty:
        return {
            "risk_level": "INSUFFICIENT_DATA",
            "success_rate": 0.0,
            "total_attempts": 0,
            "successful_optimizations": 0,
            "rollbacks": 0,
            "average_improvement": 0.0
        }

    optimization_decisions = history[
        history["decision"].isin(
            ["KEEP INDEX", "ROLLBACK"]
        )
    ]

    total_attempts = len(optimization_decisions)

    successful_optimizations = len(
        optimization_decisions[
            optimization_decisions["decision"] == "KEEP INDEX"
        ]
    )

    rollbacks = len(
        optimization_decisions[
            optimization_decisions["decision"] == "ROLLBACK"
        ]
    )

    if total_attempts == 0:
        return {
            "risk_level": "INSUFFICIENT_DATA",
            "success_rate": 0.0,
            "total_attempts": 0,
            "successful_optimizations": 0,
            "rollbacks": 0,
            "average_improvement": 0.0
        }

    success_rate = (
        successful_optimizations / total_attempts
    ) * 100

    average_improvement = (
        optimization_decisions["improvement_percent"]
        .dropna()
        .mean()
    )

    if pd.isna(average_improvement):
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
        "risk_level": risk_level,
        "success_rate": success_rate,
        "total_attempts": total_attempts,
        "successful_optimizations": successful_optimizations,
        "rollbacks": rollbacks,
        "average_improvement": average_improvement
    }


def determine_optimization_policy(
    learning_risk,
    plan_diagnosis=None
):
    if plan_diagnosis == "SLOW_WITH_INDEX":
        return {
            "policy": "PROTECTIVE",
            "optimization_allowed": False
        }

    if plan_diagnosis == "INDEXED_AND_WITHIN_THRESHOLD":
        return {
            "policy": "MONITORING",
            "optimization_allowed": False
        }

    if plan_diagnosis == "REVIEW_QUERY_AND_RESOURCES":
        return {
            "policy": "PROTECTIVE",
            "optimization_allowed": False
        }

    if learning_risk == "LOW":
        return {
            "policy": "AUTONOMOUS",
            "optimization_allowed": True
        }

    if learning_risk == "MEDIUM":
        return {
            "policy": "CAUTIOUS",
            "optimization_allowed": True
        }

    if learning_risk == "INSUFFICIENT_DATA":
        return {
            "policy": "EXPLORATORY",
            "optimization_allowed": True
        }

    return {
        "policy": "PROTECTIVE",
        "optimization_allowed": False
    }


def make_decision(analysis, predicted_latency=None):
    slow_queries = analysis["slow_queries"]

    learning = calculate_learning_risk()

    print(
        f"\nHistorical optimization success: "
        f"{learning['success_rate']:.2f}%"
    )

    print(
        f"Learning risk level: "
        f"{learning['risk_level']}"
    )

    if slow_queries.empty:
        print("\nNo slow queries detected.")

        return {
            "action": "MONITOR",
            "metric_id": None,
            "query_text": None,
            "table": None,
            "column": None,
            "filter_column": None,
            "order_column": None,
            "order_direction": None,
            "learning_risk": learning["risk_level"],
            "learning_policy": "MONITORING",
            "plan_status": "NORMAL"
        }

    selected = slow_queries.sort_values(
        "execution_time_ms",
        ascending=False
    ).iloc[0]

    metric_id = int(selected["metric_id"])
    query_text = selected["query_text"]
    execution_time = float(selected["execution_time_ms"])

    print("\nProblem detected: Slow query")
    print(f"Metric ID: {metric_id}")
    print(f"Execution time: {execution_time:.3f} ms")
    print("Query:")
    print(f"    {query_text}")

    print(
        "\nRunning query-plan analysis before optimization..."
    )

    try:
        plan_result = analyze_query_plan(query_text)

        plan_status = (
            plan_result.get("status")
            or plan_result.get("diagnosis")
            or plan_result.get("query_plan_status")
            or plan_result.get("plan_status")
        )

        if isinstance(plan_status, dict):
            plan_status = (
                plan_status.get("status")
                or plan_status.get("type")
                or plan_status.get("diagnosis")
            )

        if plan_status is None:
            plan_status = "UNKNOWN"

        plan_status = str(plan_status).upper()

        plan_recommendation = (
            plan_result.get("recommended_action")
            or plan_result.get("recommendation")
            or plan_result.get("recommended")
        )

        candidates = plan_result.get(
            "optimization_candidates",
            []
        )

        if candidates is None:
            candidates = []

        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue

            candidate_type = str(
                candidate.get("type", "")
            ).upper()

            if candidate_type == "COMPOSITE_INDEX_CANDIDATE":
                plan_status = "COMPOSITE_INDEX_CANDIDATE"

                if plan_recommendation is None:
                    plan_recommendation = (
                        candidate.get(
                            "recommended_action"
                        )
                        or "TEST_COMPOSITE_INDEX"
                    )

                break

        print(
            f"\nQuery-plan status: {plan_status}"
        )

        if plan_recommendation:
            print(
                f"Plan recommendation: "
                f"{plan_recommendation}"
            )

    except Exception as error:
        print("\nQuery-plan analysis failed.")
        print(f"Reason: {error}")

        return {
            "action": "ANALYZE_WORKLOAD",
            "metric_id": metric_id,
            "query_text": query_text,
            "table": None,
            "column": None,
            "filter_column": None,
            "order_column": None,
            "order_direction": None,
            "learning_risk": learning["risk_level"],
            "learning_policy": "PROTECTIVE",
            "plan_status": "ANALYSIS_FAILED"
        }

    policy = determine_optimization_policy(
        learning["risk_level"],
        plan_status
    )

    print(
        f"\nLearning policy: {policy['policy']}"
    )

    print(
        f"Optimization allowed: "
        f"{'YES' if policy['optimization_allowed'] else 'NO'}"
    )

    # =========================================================
    # COMPOSITE INDEX CANDIDATE
    # =========================================================

    if plan_status == "COMPOSITE_INDEX_CANDIDATE":

        composite_target = extract_composite_index_target(
            query_text
        )

        if composite_target is None:
            print(
                "\nComposite index candidate detected, "
                "but the target could not be safely extracted."
            )

            return {
                "action": "ANALYZE_WORKLOAD",
                "metric_id": metric_id,
                "query_text": query_text,
                "table": None,
                "column": None,
                "filter_column": None,
                "order_column": None,
                "order_direction": None,
                "learning_risk": learning["risk_level"],
                "learning_policy": policy["policy"],
                "plan_status": plan_status
            }

        print(
            "\nComposite index candidate detected."
        )

        print(
            "Target table: "
            f"{composite_target['table']}"
        )

        print(
            "Filter column: "
            f"{composite_target['filter_column']}"
        )

        print(
            "Order column: "
            f"{composite_target['order_column']}"
        )

        print(
            "Order direction: "
            f"{composite_target['order_direction']}"
        )

        print(
            "Suggested index: "
            f"({composite_target['filter_column']}, "
            f"{composite_target['order_column']} "
            f"{composite_target['order_direction']})"
        )

        if policy["optimization_allowed"]:

            print(
                "\nDecision: OPTIMIZE_COMPOSITE_INDEX"
            )

            return {
                "action": "OPTIMIZE_COMPOSITE_INDEX",
                "metric_id": metric_id,
                "query_text": query_text,
                "table": composite_target["table"],
                "column": composite_target["filter_column"],
                "filter_column": composite_target[
                    "filter_column"
                ],
                "order_column": composite_target[
                    "order_column"
                ],
                "order_direction": composite_target[
                    "order_direction"
                ],
                "learning_risk": learning["risk_level"],
                "learning_policy": policy["policy"],
                "plan_status": plan_status
            }

        print(
            "\nComposite optimization blocked "
            "by the current learning safety policy."
        )

        return {
            "action": "ANALYZE_WORKLOAD",
            "metric_id": metric_id,
            "query_text": query_text,
            "table": composite_target["table"],
            "column": composite_target["filter_column"],
            "filter_column": composite_target[
                "filter_column"
            ],
            "order_column": composite_target[
                "order_column"
            ],
            "order_direction": composite_target[
                "order_direction"
            ],
            "learning_risk": learning["risk_level"],
            "learning_policy": policy["policy"],
            "plan_status": plan_status
        }

    # =========================================================
    # SLOW QUERY WITH EXISTING INDEX
    # =========================================================

    if plan_status == "SLOW_WITH_INDEX":

        print(
            "\nDecision: REVIEW_QUERY_AND_RESOURCES"
        )

        return {
            "action": "ANALYZE_WORKLOAD",
            "metric_id": metric_id,
            "query_text": query_text,
            "table": None,
            "column": None,
            "filter_column": None,
            "order_column": None,
            "order_direction": None,
            "learning_risk": learning["risk_level"],
            "learning_policy": policy["policy"],
            "plan_status": plan_status
        }

    # =========================================================
    # HEALTHY INDEXED QUERY
    # =========================================================

    if plan_status == "INDEXED_AND_WITHIN_THRESHOLD":

        print(
            "\nDecision: MONITOR"
        )

        return {
            "action": "MONITOR",
            "metric_id": metric_id,
            "query_text": query_text,
            "table": None,
            "column": None,
            "filter_column": None,
            "order_column": None,
            "order_direction": None,
            "learning_risk": learning["risk_level"],
            "learning_policy": policy["policy"],
            "plan_status": plan_status
        }

    # =========================================================
    # SEQUENTIAL SCAN
    # =========================================================

    if plan_status == "SEQUENTIAL_SCAN":

        target = extract_query_target(query_text)

        if target is not None and policy["optimization_allowed"]:

            print(
                "\nDecision: OPTIMIZE_INDEX"
            )

            return {
                "action": "OPTIMIZE_INDEX",
                "metric_id": metric_id,
                "query_text": query_text,
                "table": target["table"],
                "column": target["column"],
                "filter_column": None,
                "order_column": None,
                "order_direction": None,
                "learning_risk": learning["risk_level"],
                "learning_policy": policy["policy"],
                "plan_status": plan_status
            }

        print(
            "\nDecision: ANALYZE_WORKLOAD"
        )

        return {
            "action": "ANALYZE_WORKLOAD",
            "metric_id": metric_id,
            "query_text": query_text,
            "table": (
                target["table"]
                if target is not None
                else None
            ),
            "column": (
                target["column"]
                if target is not None
                else None
            ),
            "filter_column": None,
            "order_column": None,
            "order_direction": None,
            "learning_risk": learning["risk_level"],
            "learning_policy": policy["policy"],
            "plan_status": plan_status
        }

    # =========================================================
    # FALLBACK
    # =========================================================

    print(
        "\nDecision: ANALYZE_WORKLOAD"
    )

    return {
        "action": "ANALYZE_WORKLOAD",
        "metric_id": metric_id,
        "query_text": query_text,
        "table": None,
        "column": None,
        "filter_column": None,
        "order_column": None,
        "order_direction": None,
        "learning_risk": learning["risk_level"],
        "learning_policy": policy["policy"],
        "plan_status": plan_status
    }


if __name__ == "__main__":

    df = load_metrics()

    if len(df) < 10:

        print(
            f"Not enough performance data. "
            f"Available records: {len(df)}"
        )

    else:

        df["is_anomaly"] = detect_anomalies(df)

        analysis = analyze_workload(df)

        decision = make_decision(
            analysis
        )

        print("\nDecision:")
        print(
            f"Action: {decision['action']}"
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