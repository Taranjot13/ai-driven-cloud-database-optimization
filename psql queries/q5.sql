CREATE TABLE query_performance (
    metric_id BIGSERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    execution_time_ms NUMERIC(12,3),
    rows_returned INTEGER,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

SELECT *
FROM query_performance;

SELECT
    metric_id,
    query_text,
    execution_time_ms,
    rows_returned,
    recorded_at
FROM query_performance
ORDER BY recorded_at DESC;

SELECT COUNT(*) AS total_metrics
FROM query_performance;

SELECT
    metric_id,
    ROUND(execution_time_ms, 3) AS execution_time_ms,
    rows_returned,
    recorded_at
FROM query_performance
ORDER BY metric_id DESC
LIMIT 20;

SELECT
    metric_id,
    ROUND(execution_time_ms, 3) AS execution_time_ms,
    rows_returned,
    recorded_at
FROM query_performance
ORDER BY execution_time_ms DESC
LIMIT 10;

DROP INDEX IF EXISTS idx_orders_customer_id;
