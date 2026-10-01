# Project Structure

This document lists the current repository layout for the AI-driven database optimization platform and the working demonstration dashboard.

```text
ai-driven-cloud-database-optimization/
├── .env.example
├── .gitignore
├── LICENSE
├── PROJECT_STRUCTURE.md
├── README.md
├── requirements.txt
├── start-local.ps1
├── database/
│   └── schema/
│       └── init.sql
├── docs/
│   ├── EXPERIMENT_RESULTS.md
│   ├── architecture.md
│   ├── api.md
│   ├── frontend.md
│   ├── experiments.md
│   └── graphs/
│       ├── anomaly_detection.png
│       ├── cost_breakdown.png
│       ├── latency_distribution.png
│       ├── optimization_outcomes.png
│       ├── query_latency.png
│       └── successful_optimization_improvement.png
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── api/
│       │   └── client.js
│       ├── components/
│       │   ├── DataTable.jsx
│       │   ├── Header.jsx
│       │   ├── LoadingState.jsx
│       │   ├── MetricCard.jsx
│       │   ├── Sidebar.jsx
│       │   └── StatusBadge.jsx
│       ├── main.jsx
│       ├── pages/
│       │   ├── Anomalies.jsx
│       │   ├── Costs.jsx
│       │   ├── Dashboard.jsx
│       │   ├── Optimizations.jsx
│       │   ├── Performance.jsx
│       │   ├── Predictions.jsx
│       │   ├── Resources.jsx
│       │   └── System.jsx
│       └── styles.css
├── psql queries/
│   ├── q1.sql
│   ├── q2.sql
│   ├── q3.sql
│   ├── q4.sql
│   ├── q5.sql
│   └── q6.sql
├── scripts/
│   ├── analyze_query.py
│   ├── anomaly_detection.py
│   ├── autonomous_optimizer.py
│   ├── composite_index_optimizer.py
│   ├── cost_optimizer.py
│   ├── db_config.py
│   ├── decision_engine.py
│   ├── detect_slow_queries.py
│   ├── generate_data.py
│   ├── generate_graphs.py
│   ├── generate_results.py
│   ├── index_recommender.py
│   ├── learning_engine.py
│   ├── monitor_database.py
│   ├── optimization_recommender.py
│   ├── query_plan_analyzer.py
│   ├── resource_optimizer.py
│   ├── safe_optimizer.py
│   ├── validate_index.py
│   ├── workload_generator.py
│   └── workload_prediction.py
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   └── services.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── main.py
│   ├── database/
│   │   └── __init__.py
│   ├── ml/
│   │   └── __init__.py
│   └── monitoring/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   └── test_core_components.py
└── .venv/   (local environment; ignored by Git)
```

## Notes

- Local virtual environments and generated build artifacts are excluded from version control.
- The project remains cloud-agnostic and does not include provider-specific deployment logic.
- The empty placeholder folder under `database/queries` was removed to keep the repository tree accurate.