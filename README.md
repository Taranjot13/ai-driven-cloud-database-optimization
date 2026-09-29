# AI-Driven Autonomous Cloud Database Optimization System

An intelligent database optimization system for monitoring, analyzing, predicting, and autonomously improving database performance, resource utilization, and infrastructure efficiency.

## 🚀 Project Overview

Modern cloud and enterprise databases experience continuously changing workloads that can result in slow queries, inefficient resource utilization, performance degradation, and increased infrastructure costs.

This project aims to develop an intelligent database optimization system that continuously observes database workloads and performance metrics, identifies optimization opportunities, predicts workload behavior, and safely recommends or executes optimization actions.

The system follows an autonomous optimization feedback loop:

**Monitor → Analyze → Predict → Decide → Optimize → Verify → Learn**

The long-term objective is to enable the system to make optimization decisions while maintaining predefined performance and safety constraints.

## 🎯 Core Objective

The primary objective of this project is to develop an intelligent and eventually autonomous database optimization framework capable of:

* Monitoring database performance and workload behavior
* Detecting abnormal performance patterns
* Analyzing SQL query execution performance
* Predicting future workload behavior
* Identifying database optimization opportunities
* Recommending appropriate optimization actions
* Estimating the potential impact of optimization actions
* Safely executing selected optimizations
* Verifying the effectiveness of applied changes
* Rolling back changes that negatively affect performance
* Learning from historical optimization outcomes

## 🧠 Key Technologies

* **Python** — Core development and automation
* **PostgreSQL** — Database platform and performance experimentation
* **Pandas & NumPy** — Data processing and analysis
* **Scikit-learn** — Machine learning and anomaly detection
* **XGBoost** — Workload prediction and advanced ML models
* **FastAPI** — Backend API layer
* **Prometheus** — Metrics collection
* **Grafana** — Monitoring and visualization
* **Docker** — Containerization
* **React** — Web-based monitoring dashboard
* **GitHub Actions** — CI/CD and automated testing

The architecture is designed to remain **cloud-agnostic** and can be adapted to different cloud database and infrastructure environments.

## 🏗️ Major Components

### 1. Database Monitoring

Collects database performance and workload metrics such as query execution time, returned rows, and workload activity.

### 2. SQL Query Performance Analysis

Analyzes SQL queries and their execution plans to identify inefficient query patterns.

### 3. Workload Prediction

Uses historical workload data to predict future database activity and potential performance requirements.

### 4. Anomaly Detection

Uses machine learning techniques to identify unusual database performance behavior.

### 5. Index Optimization

Identifies queries that may benefit from indexes and evaluates the performance impact of recommended indexes.

### 6. Query Optimization

Analyzes inefficient queries and identifies opportunities for improving query execution performance.

### 7. Cloud Resource Optimization

Analyzes resource utilization and recommends appropriate resource allocation or scaling decisions.

### 8. Cost Optimization

Estimates the infrastructure cost impact of different resource configurations and optimization decisions.

### 9. Autonomous Decision Engine

Acts as the decision-making layer that evaluates monitoring information, ML predictions, optimization recommendations, and system constraints to determine appropriate actions.

### 10. Safety and Rollback Mechanism

Validates optimization results before permanently applying changes and provides a mechanism for reverting ineffective or unsafe optimizations.

## 🔄 Autonomous Optimization Architecture

The intended optimization workflow is:

**Observe → Analyze → Predict → Plan → Act → Verify → Learn**

Where:

* **Observe** — Collect database and workload metrics
* **Analyze** — Identify performance problems
* **Predict** — Forecast workload and performance behavior
* **Plan** — Select an appropriate optimization strategy
* **Act** — Execute a safe optimization
* **Verify** — Measure the effect of the change
* **Learn** — Store the result for future optimization decisions

This architecture allows the project to evolve from ML-assisted automation into a more autonomous, agent-based optimization system.

## 📊 Evaluation Metrics

The system will be evaluated using quantitative performance and efficiency metrics, including:

* Query latency
* P95/P99 latency
# AI-Driven Cloud Database Optimization

A Python and PostgreSQL prototype that measures query performance, detects anomalous workload behavior, predicts the next execution time, and selects database index optimizations through an autonomous decision loop.

## Project Structure

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for the complete repository
inventory, including empty directories and all tracked files.

The main areas are:

- `database/` — PostgreSQL bootstrap schema and query directories
- `psql queries/` — Example SQL workloads
- `scripts/` — Database analysis and optimization tools
- `src/` — Application packages and orchestration entry point
- `tests/` — Test package

## Current workflow

**Monitor -> Analyze -> Predict -> Decide -> Optimize -> Verify -> Learn**

## Requirements

- Python 3.10 or later
- PostgreSQL 13 or later
- A PostgreSQL database named `cloud_optimizer`
- Tables named `query_performance` and `optimization_history`

Database settings are loaded from a local `.env` file. Copy `.env.example` to `.env` and update `DB_PASSWORD` for your PostgreSQL installation. The `.env` file is ignored by Git; never commit real credentials.

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

## Run the optimizer

```powershell
python -m src.main
```

The autonomous optimization stages require at least 10 rows in `query_performance`.
Edit `.env` with your PostgreSQL connection settings. The database and required tables (`query_performance` and `optimization_history`) must exist before running the optimizer.

## Prepare a local demo database

Create the database once, then initialize its tables from the repository root:

```powershell
psql -U postgres -c "CREATE DATABASE cloud_optimizer;"
psql -U postgres -d cloud_optimizer -f database/schema/init.sql
```

To populate the commerce tables with synthetic workload data, run:

```powershell
python -m scripts.generate_data
```

The generator creates 265,000 rows across customers, products, orders, order items, and payments. It can take time to complete. Use a disposable development database because the optimizer can create and remove indexes.

## Run tests

```powershell
python -m pytest -q
```

The autonomous optimization stages require at least 10 rows in `query_performance`.

## Safety notes

Run the optimizer against a development or staging database first. Review generated index changes and use a database user with only the permissions required for testing. The optimizer can execute schema changes when the decision engine selects an optimization.

## Project status

PostgreSQL monitoring, query analysis, workload prediction, autonomous index optimization, and learning signals are implemented. Cloud-provider resource optimization and production configuration management are not yet included.

## Author

Taranjot Singh
