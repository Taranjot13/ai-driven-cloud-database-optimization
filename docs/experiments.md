# Experiment methodology

This project evaluates the autonomous optimization workflow using a local PostgreSQL dataset with query performance, slow-query indicators, anomaly observations, and decision-history records.

## Data collection

The repository collects latency and rows-returned observations from PostgreSQL. Those values are stored in `query_performance` and used to produce operational summaries and anomaly analysis.

## Metrics

The system measures:

- average latency
- median latency
- P95 latency
- P99 latency
- maximum latency
- slow-query count
- anomaly count
- optimization outcome rate
- average successful improvement
- overall average improvement

## Safety and interpretation

The report distinguishes the following decision categories:

- `KEEP`
- `KEEP INDEX`
- `EXISTING INDEX VERIFIED`
- `EXISTING INDEX`
- `EXISTING INDEX NOT VERIFIED`
- `MEASUREMENT UNSTABLE`
- `ROLLBACK`

Successful and verified outcomes are reported separately from unstable and rolled-back experiments. The overall average improvement remains a historical aggregate and should not be treated as evidence of successful optimization performance.

## Experiment results

Current branch results are documented in `docs/EXPERIMENT_RESULTS.md`.
