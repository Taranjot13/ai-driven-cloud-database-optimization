# AI-Driven Autonomous Cloud Database Optimization System

This project is a cloud-agnostic PostgreSQL monitoring and optimization platform that observes database behavior, identifies slow-query patterns, analyzes execution plans, detects anomalies, predicts future latency, and applies safe index recommendations when the system decides the risk is acceptable.

The implemented system follows the loop:

Observe → Analyze → Predict → Decide → Act → Verify → Learn

It is designed for demonstration and research use in a local development database and intentionally avoids direct cloud-provider assumptions. The project exposes a FastAPI backend and a Vite + React dashboard so the optimization workflow is understandable in a professional observability interface.

## Implemented capabilities

- PostgreSQL performance collection and monitoring
- Slow-query detection and workload review
- Query execution analysis and target extraction
- Isolation Forest anomaly detection
- Workload prediction based on historical latency data
- Autonomous decision-making around index optimization and safety constraints
- Optimization history tracking and learning-risk evaluation
- Resource health and cost analysis using a cloud-agnostic reference model
- FastAPI read-only monitoring endpoints and explicit optimization execution routes
- Responsive React dashboard with charts, summary cards, and operational pages

## What is not claimed

The project does not claim to provide production AWS, Azure, or GCP deployment, cloud auto-scaling, Prometheus/Grafana-managed monitoring, or Docker-based production infrastructure. Those are possible future extensions, but they are not part of the implemented stack in this repository.

## Tech stack

- Python
- PostgreSQL
- SQLAlchemy
- Pandas
- Scikit-learn
- FastAPI
- React
- Vite
- Recharts
- Pytest

## Repository layout

- `database/` — PostgreSQL schema bootstrap and example workload assets
- `scripts/` — core database monitoring, optimization, prediction, cost, and safety logic
- `src/` — application configuration and FastAPI API layer
- `tests/` — unit and API test coverage
- `frontend/` — Vite + React dashboard
- `docs/` — architecture, API references, experiment results, and generated charts
- `psql queries/` — SQL workload examples
- `start-local.ps1` — single-command local launcher for API + frontend

## Local setup

### 1. Create the Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 2. Configure environment variables

Copy the example file and update credentials for your PostgreSQL instance:

```powershell
Copy-Item .env.example .env
```

The default values are:

- `DB_HOST=localhost`
- `DB_PORT=5432`
- `DB_NAME=cloud_optimizer`
- `DB_USER=postgres`
- `DB_PASSWORD=change_me`
- `API_HOST=127.0.0.1`
- `API_PORT=8000`
- `FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`

Do not commit `.env` or any real secrets.

### 3. Prepare PostgreSQL

Create the database and initialize schema if needed:

```powershell
psql -U postgres -c "CREATE DATABASE cloud_optimizer;"
psql -U postgres -d cloud_optimizer -f database/schema/init.sql
```

Optionally generate workload data:

```powershell
python -m scripts.generate_data
```

### 4. Run the backend API

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn src.api:app --reload --host 127.0.0.1 --port 8000
```

### 5. Run the full app with one command

From the repository root, run:

```powershell
./start-local.ps1
```

This starts the FastAPI backend and the Vite frontend together and opens the site at:

- http://localhost:5173

If you want to run the frontend manually instead, use:

```powershell
cd frontend
npm install
npm run dev
```

## Safety model

The optimization workflow is intentionally conservative:

- Monitoring and dashboard views are read-only by default.
- Optimization execution requires an explicit user action and confirmation.
- The existing safety and rollback logic is preserved instead of bypassing it.
- The system does not silently create or drop indexes without review.

## API overview

The backend exposes endpoints for health, dashboard data, performance, anomalies, predictions, optimization history, resources, costs, and system status.

Key routes include:

- `GET /api/health`
- `GET /api/dashboard`
- `GET /api/performance`
- `GET /api/performance/summary`
- `GET /api/anomalies`
- `GET /api/predictions`
- `GET /api/optimization/history`
- `GET /api/optimization/summary`
- `GET /api/resources`
- `GET /api/costs`
- `GET /api/system/status`
- `POST /api/optimization/analyze`
- `POST /api/optimization/execute`

## Testing

The Python test suite can be executed with:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -q
```

The frontend production build is verified with:

```powershell
cd frontend
npm run build
```

## Documentation

Additional project documentation is available in:

- `docs/architecture.md`
- `docs/api.md`
- `docs/frontend.md`
- `docs/experiments.md`
- `docs/EXPERIMENT_RESULTS.md`

## Future extensions

Potential next steps include richer operator workflows, A/B evaluations, production telemetry integrations, and deeper cloud-agnostic infrastructure modeling. This project is intentionally scoped to a safe research and university-demonstration environment.

## Author

Taranjot Singh
