# Experiment Results

This document reflects the current PostgreSQL performance and optimization history for the project. The figures are based on the repository's live data and are presented without fabricating additional results.

The metrics below distinguish successful and verified outcomes from neutral index records, unstable experiments, and rollbacks so the system's safety model remains explicit.

## 1. Performance Dataset

- Historical observations: **62**
- Slow-query threshold: **5.0 ms**
- Slow-query observations: **5**

## 2. Query Performance

| Metric | Value |
|---|---:|
| Average latency | 2.393 ms |
| Median latency | 1.698 ms |
| P95 latency | 6.365 ms |
| P99 latency | 7.106 ms |
| Minimum latency | 0.522 ms |
| Maximum latency | 7.183 ms |

## 3. Slow Query Observations

| Metric ID | Execution Time (ms) | Rows Returned |
|---:|---:|---:|
| 60 | 7.183 | 6 |
| 3 | 7.056 | 3 |
| 1 | 6.686 | 6 |
| 61 | 6.376 | 6 |
| 6 | 6.156 | 0 |

## 4. Machine Learning Anomaly Detection

- Detected anomalies: **7**
- Detection method: **Isolation Forest**
- Features used: **execution time and rows returned**

## 5. Optimization Outcomes

| Outcome | Attempts | Average Improvement |
|---|---:|---:|
| Successful / verified | 15 | +38.35% |
| Neutral existing-index records | 2 | N/A |
| Unsuccessful / unstable | 8 | See decision breakdown |
| Rollbacks | 1 | Safety outcome |
| All recorded attempts | 25 | -4.67% |

- Successful/verified outcome rate: **60.00%**
- Verified existing indexes: **4**

The overall average improvement includes unstable and rolled-back experiments and therefore should not be interpreted as the performance improvement achieved by successful optimizations. The successful/verified improvement is reported separately.

## 6. Optimization Decision Breakdown

| Decision | Attempts | Average Improvement |
|---|---:|---:|
| KEEP | 9 | 39.10% |
| EXISTING INDEX VERIFIED | 4 | 33.94% |
| EXISTING INDEX NOT VERIFIED | 4 | -121.83% |
| MEASUREMENT UNSTABLE | 3 | -46.98% |
| EXISTING INDEX | 2 | 3.79% |
| KEEP INDEX | 2 | 43.82% |
| ROLLBACK | 1 | -71.45% |

## 7. Learning Engine

- Total optimization attempts: **3**
- Successful optimizations: **2**
- Rollbacks: **1**
- Success rate: **66.67%**
- Average improvement: **5.39%**
- Risk level: **MEDIUM**

The learning-engine snapshot is generated from its current historical-success logic. The detailed optimization-outcome section above uses the individual optimization-history decision categories for experimental reporting.

## 8. Resource Health

- Overall resource status: **WARNING**
- Connection utilization: **2.00%**
- Cache hit ratio: **98.04%**
- Rollback rate: **37.36%**
- Database size: **0.0345 GB**

## 9. Cost Analysis

- Cost status: **COST_EFFICIENT**
- Estimated monthly compute cost: **$50.00**
- Estimated monthly storage cost: **$0.00**
- Estimated monthly connection cost: **$0.55**
- Estimated monthly total cost: **$50.55**

The cost values are produced by the project's cloud-agnostic reference pricing model and should not be interpreted as actual billing from a specific cloud provider.

## 10. Interpretation

The current experimental dataset demonstrates that the system can collect database performance observations, identify slow-query events, detect anomalous behavior, evaluate resource and cost conditions, and maintain historical records of optimization outcomes.

The optimization results also demonstrate the role of safety controls. Successful and verified changes are separated from unstable experiments and rollbacks, allowing the decision engine to consider previous outcomes when selecting future actions.

## 11. Reproducibility

This report is generated from the project's current PostgreSQL performance and optimization-history tables. Running the script again after additional workload collection will refresh the reported values.
