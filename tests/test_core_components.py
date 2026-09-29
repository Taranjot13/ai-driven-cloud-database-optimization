import pandas as pd

from scripts.decision_engine import (
    analyze_workload,
    detect_anomalies,
    extract_query_target,
    determine_optimization_policy,
)


def test_analyze_workload():
    df = pd.DataFrame(
        [
            {
                "metric_id": 1,
                "query_text": "SELECT * FROM orders;",
                "execution_time_ms": 2.0,
                "rows_returned": 5,
                "recorded_at": "2026-09-14 10:00:00",
            },
            {
                "metric_id": 2,
                "query_text": "SELECT * FROM orders WHERE customer_id = 5000;",
                "execution_time_ms": 7.0,
                "rows_returned": 6,
                "recorded_at": "2026-09-14 10:01:00",
            },
        ]
    )

    result = analyze_workload(df)

    assert result["average_latency"] == 4.5
    assert result["latest_latency"] == 7.0
    assert result["maximum_latency"] == 7.0
    assert result["slow_queries"] == 1
    assert result["latest_metric_id"] == 2


def test_extract_query_target():
    query = """
        SELECT o.order_id
        FROM orders o
        WHERE o.customer_id = 5000
        ORDER BY o.order_date DESC;
    """

    result = extract_query_target(query)

    assert result["table_name"] == "orders"
    assert result["column_name"] == "customer_id"
    assert result["order_column"] == "order_date"
    assert result["order_direction"] == "DESC"


def test_extract_simple_query_target():
    query = """
        SELECT *
        FROM products
        WHERE category = 'Electronics';
    """

    result = extract_query_target(query)

    assert result["table_name"] == "products"
    assert result["column_name"] == "category"
    assert result["order_column"] is None
    assert result["order_direction"] is None


def test_detect_anomalies_with_sufficient_data():
    rows = []

    for i in range(20):
        rows.append(
            {
                "metric_id": i + 1,
                "query_text": "SELECT * FROM orders;",
                "execution_time_ms": 2.0,
                "rows_returned": 5,
                "recorded_at": f"2026-09-14 10:{i:02d}:00",
            }
        )

    df = pd.DataFrame(rows)

    result = detect_anomalies(df)

    assert "anomaly" in result.columns
    assert "status" in result.columns
    assert len(result) == 20


def test_detect_anomalies_with_insufficient_data():
    df = pd.DataFrame(
        [
            {
                "metric_id": 1,
                "query_text": "SELECT 1;",
                "execution_time_ms": 1.0,
                "rows_returned": 1,
                "recorded_at": "2026-09-14 10:00:00",
            }
        ]
    )

    result = detect_anomalies(df)

    assert len(result) == 1


def test_resource_protective_policy():
    result = determine_optimization_policy(
        learning_risk="MEDIUM",
        plan_diagnosis=None,
        resource_status="CRITICAL",
        cost_status="COST_EFFICIENT",
    )

    assert result["policy"] == "RESOURCE_PROTECTIVE"
    assert result["optimization_allowed"] is False


def test_cost_protective_policy():
    result = determine_optimization_policy(
        learning_risk="MEDIUM",
        plan_diagnosis=None,
        resource_status="HEALTHY",
        cost_status="HIGH_COST_RISK",
    )

    assert result["policy"] == "COST_PROTECTIVE"
    assert result["optimization_allowed"] is False


def test_high_learning_risk_policy():
    result = determine_optimization_policy(
        learning_risk="HIGH",
        plan_diagnosis=None,
        resource_status="HEALTHY",
        cost_status="COST_EFFICIENT",
    )

    assert result["policy"] == "CONSERVATIVE"
    assert result["optimization_allowed"] is False


def test_medium_learning_risk_policy():
    result = determine_optimization_policy(
        learning_risk="MEDIUM",
        plan_diagnosis=None,
        resource_status="HEALTHY",
        cost_status="COST_EFFICIENT",
    )

    assert result["policy"] == "CAUTIOUS"
    assert result["optimization_allowed"] is True
