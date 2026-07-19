-- window_functions.sql
-- Step 5: SQL Analytics - Window Functions & CTEs
-- Dialect: SQLite (3.25+, required for window function support)

-- ============================================================
-- 1. Rank customers by lifetime value (RANK / DENSE_RANK)
-- ============================================================
WITH customer_ltv AS (
    SELECT
        c.customer_id,
        c.first_name || ' ' || c.last_name AS customer_name,
        c.segment,
        ROUND(SUM(oi.quantity * oi.unit_price), 2) AS lifetime_value
    FROM customers c
    JOIN orders o        ON o.customer_id = c.customer_id
    JOIN order_items oi  ON oi.order_id = o.order_id
    WHERE o.status IN ('completed', 'pending')
    GROUP BY c.customer_id, c.first_name, c.last_name, c.segment
)
SELECT
    customer_id,
    customer_name,
    segment,
    lifetime_value,
    RANK()       OVER (ORDER BY lifetime_value DESC) AS ltv_rank,
    DENSE_RANK() OVER (ORDER BY lifetime_value DESC) AS ltv_dense_rank,
    RANK()       OVER (PARTITION BY segment ORDER BY lifetime_value DESC) AS rank_within_segment
FROM customer_ltv
ORDER BY ltv_rank
LIMIT 30;


-- ============================================================
-- 2. Running total and moving average of monthly revenue
-- ============================================================
WITH monthly_revenue AS (
    SELECT
        strftime('%Y-%m', o.order_date) AS order_month,
        ROUND(SUM(oi.quantity * oi.unit_price), 2) AS monthly_total
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status IN ('completed', 'pending')
    GROUP BY order_month
)
SELECT
    order_month,
    monthly_total,
    ROUND(SUM(monthly_total) OVER (ORDER BY order_month), 2) AS running_total_revenue,
    ROUND(AVG(monthly_total) OVER (
        ORDER BY order_month
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS moving_avg_3mo
FROM monthly_revenue
ORDER BY order_month;


-- ============================================================
-- 3. Month-over-month revenue growth rate (multi-step CTE)
-- ============================================================
WITH monthly_revenue AS (
    SELECT
        strftime('%Y-%m', o.order_date) AS order_month,
        ROUND(SUM(oi.quantity * oi.unit_price), 2) AS monthly_total
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status IN ('completed', 'pending')
    GROUP BY order_month
),
revenue_with_lag AS (
    SELECT
        order_month,
        monthly_total,
        LAG(monthly_total) OVER (ORDER BY order_month) AS prev_month_total
    FROM monthly_revenue
)
SELECT
    order_month,
    monthly_total,
    prev_month_total,
    CASE
        WHEN prev_month_total IS NULL OR prev_month_total = 0 THEN NULL
        ELSE ROUND(100.0 * (monthly_total - prev_month_total) / prev_month_total, 2)
    END AS mom_growth_pct
FROM revenue_with_lag
ORDER BY order_month;


-- ============================================================
-- 4. Each customer's order history with running spend total
--    (per-customer running total via PARTITION BY)
-- ============================================================
WITH order_totals AS (
    SELECT
        o.order_id,
        o.customer_id,
        o.order_date,
        SUM(oi.quantity * oi.unit_price) AS order_total
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status IN ('completed', 'pending')
    GROUP BY o.order_id, o.customer_id, o.order_date
)
SELECT
    customer_id,
    order_id,
    order_date,
    ROUND(order_total, 2) AS order_total,
    ROUND(SUM(order_total) OVER (
        PARTITION BY customer_id ORDER BY order_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 2) AS running_customer_spend
FROM order_totals
ORDER BY customer_id, order_date
LIMIT 50;
