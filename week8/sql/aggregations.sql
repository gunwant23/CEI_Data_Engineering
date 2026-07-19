-- aggregations.sql
-- Step 4: SQL Analytics - Joins & Aggregations
-- Dialect: SQLite

-- ============================================================
-- 1. Total revenue per customer
-- ============================================================
SELECT
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.segment,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue,
    COUNT(DISTINCT o.order_id) AS num_orders
FROM customers c
JOIN orders o       ON o.customer_id = c.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.status IN ('completed', 'pending')
GROUP BY c.customer_id, c.first_name, c.last_name, c.segment
ORDER BY total_revenue DESC;


-- ============================================================
-- 2. Total revenue per product category
-- ============================================================
SELECT
    p.category,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue,
    SUM(oi.quantity) AS total_units_sold,
    COUNT(DISTINCT o.order_id) AS num_orders
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
JOIN orders o   ON o.order_id = oi.order_id
WHERE o.status IN ('completed', 'pending')
GROUP BY p.category
ORDER BY total_revenue DESC;


-- ============================================================
-- 3. Total revenue per month
-- ============================================================
SELECT
    strftime('%Y-%m', o.order_date) AS order_month,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue,
    COUNT(DISTINCT o.order_id) AS num_orders
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.status IN ('completed', 'pending')
GROUP BY order_month
ORDER BY order_month;


-- ============================================================
-- 4. Top products by quantity sold and revenue
-- ============================================================
SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(oi.quantity) AS total_units_sold,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
JOIN orders o   ON o.order_id = oi.order_id
WHERE o.status IN ('completed', 'pending')
GROUP BY p.product_id, p.product_name, p.category
ORDER BY total_revenue DESC
LIMIT 20;


-- ============================================================
-- 5. Average order value (AOV) by customer segment
-- ============================================================
WITH order_totals AS (
    SELECT
        o.order_id,
        o.customer_id,
        SUM(oi.quantity * oi.unit_price) AS order_total
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status IN ('completed', 'pending')
    GROUP BY o.order_id, o.customer_id
)
SELECT
    c.segment,
    ROUND(AVG(ot.order_total), 2) AS avg_order_value,
    COUNT(ot.order_id) AS num_orders
FROM order_totals ot
JOIN customers c ON c.customer_id = ot.customer_id
GROUP BY c.segment
ORDER BY avg_order_value DESC;
