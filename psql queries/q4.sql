-- CREATE INDEX idx_orders_customer_id
-- ON orders(customer_id);
-- EXPLAIN ANALYZE
-- SELECT *
-- FROM orders
-- WHERE customer_id = 5000;
-- DROP INDEX IF EXISTS idx_orders_customer_id;
EXPLAIN ANALYZE
SELECT *
FROM orders
WHERE customer_id = 5000;

CREATE INDEX idx_orders_customer_id
ON orders(customer_id);

EXPLAIN ANALYZE
SELECT *
FROM orders
WHERE customer_id = 5000;

