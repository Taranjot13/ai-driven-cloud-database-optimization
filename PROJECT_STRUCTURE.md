# Project Structure

This document lists the project files and directories currently present in the
repository. Generated virtual-environment files, Python cache directories, and
other local build artifacts are excluded.

```text
ai-driven-cloud-database-optimization/
├── .gitignore
├── .env.example
├── LICENSE
├── README.md
├── PROJECT_STRUCTURE.md
├── requirements.txt
├── database/
│   ├── queries/                 [empty]
│   └── schema/
│       └── init.sql
├── docs/
│   ├── EXPERIMENT_RESULTS.md
│   └── graphs/
│       ├── anomaly_detection.png
│       ├── cost_breakdown.png
│       ├── latency_distribution.png
│       ├── optimization_outcomes.png
│       ├── query_latency.png
│       └── successful_optimization_improvement.png
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
│   ├── decision_engine.py
│   ├── db_config.py
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
│   ├── main.py
│   ├── config/
│   │   └── __init__.py
│   ├── database/
│   │   └── __init__.py
│   ├── ml/
│   │   └── __init__.py
│   └── monitoring/
│       └── __init__.py
└── tests/
    ├── __init__.py
    └── test_core_components.py
```

## Empty Directories

- `database/queries/`

There are currently no zero-byte files in the repository.