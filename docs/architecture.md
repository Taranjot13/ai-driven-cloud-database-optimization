# Architecture

This project is structured around a simple data-flow pipeline that keeps the existing optimization logic intact while exposing it through a safe API and a monitoring dashboard.

## Core flow

Observe → Analyze → Predict → Decide → Act → Verify → Learn

## Components

### 1. Monitoring layer

The PostgreSQL monitoring scripts collect query metrics such as latency, rows returned, and timestamps. The canonical logic lives in the scripts package and reads from the configured local database.

### 2. Analysis layer

The decision engine evaluates query workloads, computes summary statistics, and identifies slow queries. Anomaly detection uses Isolation Forest with execution time and rows returned as the main signals.

### 3. Prediction layer

The workload prediction module uses historical query performance observations to estimate the next execution latency and classify the outlook as expected or degraded.

### 4. Optimization layer

Index recommendation and optimization logic remain in the scripts package. The system identifies a target table and column, measures the effect of an index, verifies safety, and records the decision outcome in the optimization_history table.

### 5. Safety and rollback layer

The system does not execute changes without explicit confirmation. When a result is unstable or worse than expected, rollback logic is invoked to revert the attempted change and record the event.

### 6. API and frontend layer

FastAPI exposes read-only dashboards and explicit optimization actions. The React frontend visualizes the real system state and allows users to inspect data without triggering automatic database changes.

## Data sources

- `query_performance`: monitored execution metrics
- `optimization_history`: decision outcomes and measured impact
- `resource` and `cost` calculations: derived from heuristics and historical metrics

## Deployment assumptions

This repository is intentionally cloud-agnostic. It does not rely on provider-specific APIs or service integration.
