import re

import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import IsolationForest

from scripts.query_plan_analyzer import analyze_query_plan
from scripts.resource_optimizer import run_resource_optimization
from scripts.cost_optimizer import run_cost_optimization


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "cloud_optimizer",
    "user": "postgres",
    "password": "123456t"  # Replace with your actual PostgreSQL password   
}


SLOW_QUERY_THRESHOLD_MS = 5.0


def get_engine():
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


def detect_anomalies(df):
    if len(df) < 10:
        result = df.copy()
        result["anomaly"] = 1
        result["status"] = "Normal"
        return result

    result = df.copy()

    features = result[
        [
            "execution_time_ms",
            "rows_returned"
        ]
    ]

    model = IsolationForest(
        contamination=0.10,
        random_state=42
    )

    result["anomaly"] = model.fit_predict(features)

    result["status"] = result["anomaly"].map(
        {
            1: "Normal",
            -1: "Anomaly"
        }
    )

    return result


def analyze_workload(df):
    if df.empty:
        return {
            "average_latency": 0.0,
            "latest_latency": 0.0,
            "maximum_latency": 0.0,
            "slow_queries": 0,
            "latest_metric_id": None,
            "latest_query": None
        }

    average_latency = float(
        df["execution_time_ms"].mean()
    )

    latest_row = df.iloc[-1]

    latest_latency = float(
        latest_row["execution_time_ms"]
    )

    maximum_latency = float(
        df["execution_time_ms"].max()
    )

    slow_queries = int(
        (
            df["execution_time_ms"]
            > SLOW_QUERY_THRESHOLD_MS
        ).sum()
    )

    return {
        "average_latency": average_latency,
        "latest_latency": latest_latency,
        "maximum_latency": maximum_latency,
        "slow_queries": slow_queries,
        "latest_metric_id": int(
            latest_row["metric_id"]
        ),
        "latest_query": str(
            latest_row["query_text"]
        )
    }


def extract_query_target(query_text):
    if not query_text:
        return {
            "table_name": None,
            "column_name": None,
            "order_column": None,
            "order_direction": None
        }

    table_match = re.search(
        r"FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        query_text,
        re.IGNORECASE
    )

    column_match = re.search(
        r"WHERE\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=",
        query_text,
        re.IGNORECASE
    )

    order_match = re.search(
        r"ORDER\s+BY\s+([a-zA-Z_][a-zA-Z0-9_]*)(?:\s+(ASC|DESC))?",
        query_text,
        re.IGNORECASE
    )

    return {
        "table_name": (
            table_match.group(1)
            if table_match
            else None
        ),
        "column_name": (
            column_match.group(1)
            if column_match
            else None
        ),
        "order_column": (
            order_match.group(1)
            if order_match
            else None
        ),
        "order_direction": (
            order_match.group(2).upper()
            if order_match and order_match.group(2)
            else None
        )
    }


def extract_composite_index_target(query_text):
    target = extract_query_target(query_text)

    if (
        target["table_name"]
        and target["column_name"]
        and target["order_column"]
    ):
        return target

    return {
        "table_name": None,
        "column_name": None,
        "order_column": None,
        "order_direction": None
    }


def calculate_learning_risk():
    try:
        engine = get_engine()

        query = """
            SELECT
                COUNT(*) AS total_attempts,
                COUNT(*) FILTER (
                    WHERE decision IN (
                        'KEEP',
                        'EXISTING INDEX VERIFIED'
                    )
                ) AS successful,
                COUNT(*) FILTER (
                    WHERE decision = 'ROLLBACK'
                ) AS rollbacks
            FROM optimization_history;
        """

        try:
            df = pd.read_sql_query(query, engine)
        finally:
            engine.dispose()

        if df.empty:
            return {
                "total_attempts": 0,
                "successful": 0,
                "rollbacks": 0,
                "success_rate": 0.0,
                "risk_level": "LOW"
            }

        total_attempts = int(
            df.iloc[0]["total_attempts"] or 0
        )

        successful = int(
            df.iloc[0]["successful"] or 0
        )

        rollbacks = int(
            df.iloc[0]["rollbacks"] or 0
        )

        if total_attempts == 0:
            success_rate = 0.0
        else:
            success_rate = (
                successful / total_attempts
            ) * 100

        if success_rate >= 80:
            risk_level = "LOW"
        elif success_rate >= 50:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        return {
            "total_attempts": total_attempts,
            "successful": successful,
            "rollbacks": rollbacks,
            "success_rate": success_rate,
            "risk_level": risk_level
        }

    except Exception:
        return {
            "total_attempts": 0,
            "successful": 0,
            "rollbacks": 0,
            "success_rate": 0.0,
            "risk_level": "UNKNOWN"
        }


def determine_optimization_policy(
    learning_risk,
    plan_diagnosis=None,
    resource_status="HEALTHY",
    cost_status="COST_EFFICIENT"
):
    if resource_status == "CRITICAL":
        return {
            "policy": "RESOURCE_PROTECTIVE",
            "optimization_allowed": False
        }

    if cost_status == "HIGH_COST_RISK":
        return {
            "policy": "COST_PROTECTIVE",
            "optimization_allowed": False
        }

    if learning_risk == "HIGH":
        return {
            "policy": "CONSERVATIVE",
            "optimization_allowed": False
        }

    if learning_risk == "MEDIUM":
        return {
            "policy": "CAUTIOUS",
            "optimization_allowed": True
        }

    if plan_diagnosis == "SLOW_WITH_INDEX":
        return {
            "policy": "PERFORMANCE_REVIEW",
            "optimization_allowed": True
        }

    return {
        "policy": "NORMAL",
        "optimization_allowed": True
    }


def build_decision_result(
    action,
    learning,
    policy,
    plan_diagnosis,
    plan_recommendation,
    resource_result,
    cost_result,
    target
):
    return {
        "action": action,

        "learning_risk": learning["risk_level"],

        "learning_policy": policy["policy"],

        "optimization_allowed": policy[
            "optimization_allowed"
        ],

        "plan_status": plan_diagnosis,

        "plan_recommendation": plan_recommendation,

        "resource_status": resource_result[
            "status"
        ],

        "resource_recommendations": resource_result[
            "recommendations"
        ],

        "resource_metrics": {
            "connection_utilization":
                resource_result[
                    "connection_utilization"
                ],

            "cache_hit_ratio":
                resource_result[
                    "cache_hit_ratio"
                ],

            "rollback_rate":
                resource_result[
                    "rollback_rate"
                ],

            "database_size_gb":
                resource_result[
                    "database_size_gb"
                ]
        },

        "cost_status": cost_result[
            "status"
        ],

        "cost_metrics": {
            "estimated_monthly_cost":
                cost_result[
                    "estimated_monthly_cost"
                ],

            "compute_cost":
                cost_result[
                    "compute_cost"
                ],

            "storage_cost":
                cost_result[
                    "storage_cost"
                ],

            "connection_cost":
                cost_result[
                    "connection_cost"
                ]
        },

        "cost_recommendations":
            cost_result[
                "recommendations"
            ],

        "target": target
    }


def make_decision(
    analysis,
    predicted_latency=None
):
    learning = calculate_learning_risk()

    resource_result = run_resource_optimization()

    resource_status = resource_result[
        "status"
    ]

    cost_result = run_cost_optimization()

    cost_status = cost_result[
        "status"
    ]

    print(
        f"\nHistorical optimization success: "
        f"{learning['success_rate']:.2f}%"
    )

    print(
        f"Learning risk level: "
        f"{learning['risk_level']}"
    )

    print("\n===== RESOURCE HEALTH =====")

    print(
        f"Resource status: "
        f"{resource_status}"
    )

    print(
        f"Connection utilization: "
        f"{resource_result['connection_utilization']:.2f}%"
    )

    print(
        f"Cache hit ratio: "
        f"{resource_result['cache_hit_ratio']:.2f}%"
    )

    print(
        f"Rollback rate: "
        f"{resource_result['rollback_rate']:.2f}%"
    )

    print(
        f"Database size: "
        f"{resource_result['database_size_gb']:.4f} GB"
    )

    print("\nResource recommendations:")

    for recommendation in resource_result[
        "recommendations"
    ]:
        print(f"- {recommendation}")

    print("\n===== COST HEALTH =====")

    print(
        f"Cost status: "
        f"{cost_status}"
    )

    print(
        f"Estimated monthly cost: "
        f"${cost_result['estimated_monthly_cost']:.2f}"
    )

    print(
        f"Compute cost: "
        f"${cost_result['compute_cost']:.2f}"
    )

    print(
        f"Storage cost: "
        f"${cost_result['storage_cost']:.2f}"
    )

    print(
        f"Connection cost: "
        f"${cost_result['connection_cost']:.2f}"
    )

    print("\nCost recommendations:")

    for recommendation in cost_result[
        "recommendations"
    ]:
        print(f"- {recommendation}")

    target = extract_query_target(
        analysis.get("latest_query")
    )

    plan_diagnosis = None
    plan_recommendation = None

    latest_latency = analysis.get(
        "latest_latency",
        0.0
    )

    latest_query = analysis.get(
        "latest_query"
    )

    if latest_latency > SLOW_QUERY_THRESHOLD_MS:

        print(
            "\nProblem detected: Slow query"
        )

        print(
            f"Metric ID: "
            f"{analysis.get('latest_metric_id')}"
        )

        print(
            f"Execution time: "
            f"{latest_latency:.3f} ms"
        )

        print(
            f"Query:\n\n"
            f"{latest_query}"
        )

        if latest_query:

            print(
                "\nRunning query-plan analysis "
                "before optimization..."
            )

            try:
                plan_result = analyze_query_plan(
                    latest_query
                )

                if isinstance(plan_result, dict):

                    plan_diagnosis = plan_result.get(
                        "status"
                    )

                    plan_recommendation = (
                        plan_result.get(
                            "recommended_action"
                        )
                    )

                    if not plan_recommendation:
                        plan_recommendation = (
                            plan_result.get(
                                "recommendation"
                            )
                        )

            except Exception as error:
                print(
                    "\nQuery-plan analysis failed:"
                )

                print(error)

    policy = determine_optimization_policy(
        learning["risk_level"],
        plan_diagnosis,
        resource_status,
        cost_status
    )

    print(
        f"\nLearning policy: "
        f"{policy['policy']}"
    )

    print(
        f"Optimization allowed: "
        f"{'YES' if policy['optimization_allowed'] else 'NO'}"
    )

    action = "MONITOR"

    if resource_status == "CRITICAL":

        action = "RESOURCE_PROTECTION"

        print(
            "\nCritical resource pressure detected."
        )

        print(
            "Optimization blocked until resource "
            "health improves."
        )

    elif cost_status == "HIGH_COST_RISK":

        action = "COST_PROTECTION"

        print(
            "\nHigh cost risk detected."
        )

        print(
            "Optimization blocked by cost-protection policy."
        )

    elif latest_latency <= SLOW_QUERY_THRESHOLD_MS:

        action = "MONITOR"

        print(
            "\nQuery is currently within "
            "the performance threshold."
        )

        print(
            "Decision: MONITOR"
        )

    elif plan_diagnosis == "EXISTING_COMPOSITE_INDEX":

        action = (
            "VERIFY_EXISTING_COMPOSITE_INDEX"
        )

        print(
            "\nExisting composite index detected."
        )

        print(
            "Decision: "
            "VERIFY_EXISTING_COMPOSITE_INDEX"
        )

    elif (
        plan_diagnosis == "SLOW_WITH_INDEX"
    ):

        action = "ANALYZE_WORKLOAD"

        print(
            "\nQuery is using an index but "
            "remains slow."
        )

        print(
            "Decision: ANALYZE_WORKLOAD"
        )

    elif (
        plan_diagnosis == "INDEXED_AND_WITHIN_THRESHOLD"
    ):

        action = "MONITOR"

        print(
            "\nQuery is already indexed "
            "and within threshold."
        )

        print(
            "Decision: MONITOR"
        )

    elif (
        plan_diagnosis == "COMPOSITE_INDEX_CANDIDATE"
        and policy["optimization_allowed"]
    ):

        target = extract_composite_index_target(
            latest_query
        )

        if (
            target["table_name"]
            and target["column_name"]
            and target["order_column"]
        ):
            action = (
                "OPTIMIZE_COMPOSITE_INDEX"
            )

            print(
                "\nComposite index candidate detected."
            )

            print(
                "Decision: "
                "OPTIMIZE_COMPOSITE_INDEX"
            )

        else:
            action = "ANALYZE_WORKLOAD"

    elif (
        plan_recommendation == "OPTIMIZE_INDEX"
        and policy["optimization_allowed"]
    ):

        action = "OPTIMIZE_INDEX"

        print(
            "\nSingle-column index optimization "
            "recommended."
        )

        print(
            "Decision: OPTIMIZE_INDEX"
        )

    elif (
        plan_recommendation
        == "OPTIMIZE_COMPOSITE_INDEX"
        and policy["optimization_allowed"]
    ):

        action = (
            "OPTIMIZE_COMPOSITE_INDEX"
        )

        print(
            "\nComposite index optimization "
            "recommended."
        )

        print(
            "Decision: "
            "OPTIMIZE_COMPOSITE_INDEX"
        )

    elif latest_latency > SLOW_QUERY_THRESHOLD_MS:

        action = "ANALYZE_WORKLOAD"

        print(
            "\nSlow query detected, but no safe "
            "automatic modification was identified."
        )

        print(
            "Decision: ANALYZE_WORKLOAD"
        )

    else:

        action = "MONITOR"

        print(
            "\nNo optimization required."
        )

        print(
            "Decision: MONITOR"
        )

    return build_decision_result(
        action=action,
        learning=learning,
        policy=policy,
        plan_diagnosis=plan_diagnosis,
        plan_recommendation=plan_recommendation,
        resource_result=resource_result,
        cost_result=cost_result,
        target=target
    )


if __name__ == "__main__":

    df = load_metrics()

    if df.empty:

        print(
            "No performance metrics available."
        )

    else:

        analysis = analyze_workload(df)

        decision = make_decision(
            analysis
        )

        print(
            "\n===== FINAL DECISION ====="
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

        print(
            f"Resource status: "
            f"{decision['resource_status']}"
        )

        print(
            f"Cost status: "
            f"{decision['cost_status']}"
        )

        print(
            f"Estimated monthly cost: "
            f"${decision['cost_metrics']['estimated_monthly_cost']:.2f}"
        )