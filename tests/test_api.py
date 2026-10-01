from fastapi.testclient import TestClient

from src.api import app
from src.api import services


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dashboard_endpoint(monkeypatch):
    snapshot = {"performance": {"summary": {"observations": 3}}}
    monkeypatch.setattr(services, "get_dashboard", lambda: snapshot)

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    assert response.json() == snapshot


def test_performance_endpoint(monkeypatch):
    data = {"threshold_ms": 5.0, "records": []}
    monkeypatch.setattr(services, "get_performance", lambda *args: data)

    response = client.get("/api/performance?slow_only=true")

    assert response.status_code == 200
    assert response.json() == data


def test_anomaly_endpoint(monkeypatch):
    data = {"total": 1, "records": [{"metric_id": 4, "status": "Anomaly"}]}
    monkeypatch.setattr(services, "get_anomalies", lambda: data)

    response = client.get("/api/anomalies")

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_prediction_endpoint(monkeypatch):
    data = {"status": "READY", "predicted_latency_ms": 2.4}
    monkeypatch.setattr(services, "get_prediction", lambda: data)

    response = client.get("/api/predictions")

    assert response.status_code == 200
    assert response.json() == data


def test_optimization_history_endpoint(monkeypatch):
    data = {"records": [{"decision": "ROLLBACK"}]}
    monkeypatch.setattr(services, "get_optimization_history", lambda limit: data)

    response = client.get("/api/optimization/history")

    assert response.status_code == 200
    assert response.json() == data


def test_resources_endpoint(monkeypatch):
    data = {"status": "HEALTHY", "recommendations": []}
    monkeypatch.setattr(services, "get_resources", lambda: data)

    response = client.get("/api/resources")

    assert response.status_code == 200
    assert response.json() == data


def test_costs_endpoint(monkeypatch):
    monkeypatch.setattr(
        services,
        "get_costs",
        lambda: {"estimated_monthly_cost": 50.55},
    )

    response = client.get("/api/costs")

    assert response.status_code == 200
    assert response.json()["model_name"] == "Cloud-Agnostic Reference Cost Model"


def test_optimization_execution_requires_confirmation():
    response = client.post(
        "/api/optimization/execute",
        json={
            "metric_id": 1,
            "expected_action": "OPTIMIZE_INDEX",
        },
    )

    assert response.status_code == 400


def test_system_status_endpoint(monkeypatch):
    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, _query):
            return None

    class FakeEngine:
        def connect(self):
            return FakeConnection()

        def dispose(self):
            return None

    monkeypatch.setattr("src.api.routes.get_engine", lambda: FakeEngine())
    monkeypatch.setattr(
        services,
        "get_optimization_history",
        lambda limit: {"records": []},
    )

    response = client.get("/api/system/status")

    assert response.status_code == 200
    assert response.json()["database"] == "connected"