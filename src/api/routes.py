from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from scripts.decision_engine import get_engine
from src.api import services
from src.api.schemas import (
    OptimizationAnalyzeRequest,
    OptimizationExecuteRequest,
)


router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "service": "database-optimization-api"}


@router.get("/dashboard")
def dashboard():
    return services.get_dashboard()


@router.get("/performance")
def performance(
    limit: int = Query(default=500, ge=1, le=5000),
    slow_only: bool = False,
    search: str | None = Query(default=None, max_length=200),
):
    return services.get_performance(limit, slow_only, search)


@router.get("/performance/summary")
def performance_summary():
    return services.get_performance_summary()


@router.get("/slow-queries")
def slow_queries(limit: int = Query(default=500, ge=1, le=5000)):
    return services.get_performance(limit=limit, slow_only=True)


@router.get("/anomalies")
def anomalies():
    return services.get_anomalies()


@router.get("/predictions")
def predictions():
    return services.get_prediction()


@router.get("/optimization/history")
def optimization_history(
    limit: int = Query(default=500, ge=1, le=5000),
):
    return services.get_optimization_history(limit)


@router.get("/optimization/summary")
def optimization_summary():
    return services.get_optimization_summary()


@router.post("/optimization/analyze")
def analyze_optimization(request: OptimizationAnalyzeRequest):
    result = services.analyze_optimization(request.metric_id)
    if result["status"] == "NOT_FOUND":
        raise HTTPException(status_code=404, detail=result["reason"])
    return result


@router.post("/optimization/execute")
def execute_optimization(request: OptimizationExecuteRequest):
    if not request.confirmed:
        raise HTTPException(
            status_code=400,
            detail="Explicit confirmation is required to execute an optimization.",
        )
    result = services.execute_optimization(
        request.metric_id,
        request.expected_action,
    )
    if result["status"] == "STALE_PREVIEW":
        raise HTTPException(status_code=409, detail=result)
    if result["status"] == "NOT_FOUND":
        raise HTTPException(status_code=404, detail=result["reason"])
    return result


@router.get("/resources")
def resources():
    return services.get_resources()


@router.get("/costs")
def costs():
    result = services.get_costs()
    return {
        **result,
        "model_name": "Cloud-Agnostic Reference Cost Model",
        "billing_notice": (
            "Estimates are for project evaluation and are not provider billing."
        ),
    }


@router.get("/system/status")
def system_status():
    engine = get_engine()
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database_status = "connected"
    finally:
        engine.dispose()

    return {
        "status": "operational",
        "database": database_status,
        "modules": [
            "PostgreSQL monitoring",
            "Query-plan analysis",
            "Isolation Forest anomaly detection",
            "Random Forest workload prediction",
            "Safe index optimization and rollback",
            "Resource health analysis",
            "Cloud-agnostic reference cost model",
            "Optimization history learning",
        ],
        "latest_recorded_decision": (
            services.get_optimization_history(limit=1)["records"][-1]["decision"]
            if services.get_optimization_history(limit=1)["records"]
            else None
        ),
    }