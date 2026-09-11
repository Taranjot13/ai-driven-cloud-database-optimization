CREATE TABLE optimization_history (
    optimization_id BIGSERIAL PRIMARY KEY,
    metric_id BIGINT,
    optimization_type VARCHAR(100) NOT NULL,
    table_name VARCHAR(100),
    column_name VARCHAR(100),
    baseline_time_ms NUMERIC(12,3),
    optimized_time_ms NUMERIC(12,3),
    improvement_percent NUMERIC(12,3),
    decision VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

SELECT * FROM optimization_history;

SELECT *
FROM optimization_history
ORDER BY created_at DESC;





