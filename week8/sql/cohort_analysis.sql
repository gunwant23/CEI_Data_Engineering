-- cohort_analysis.sql
-- Step 6: Cohort & Retention Analysis
-- Step 7: Customer Segmentation (frequency tier, spend tier, RFM)
-- Dialect: SQLite

-- ============================================================
-- 1. Assign each customer to a cohort = month of first purchase
-- ============================================================
DROP VIEW IF EXISTS customer_cohorts;
CREATE VIEW customer_cohorts AS
SELECT
    o.customer_id,
    MIN(strftime('%Y-%m', o.order_date)) AS cohort_month
FROM orders o
WHERE o.status IN ('completed', 'pending')
GROUP BY o.customer_id;


-- ============================================================
-- 2. Monthly retention rate per cohort
--    (% of a cohort's customers who placed >=1 order in a given
--     month, indexed by "months since first purchase")
-- ============================================================
WITH orders_flagged AS (
    SELECT
        o.customer_id,
        strftime('%Y-%m', o.order_date) AS order_month,
        cc.cohort_month
    FROM orders o
    JOIN customer_cohorts cc ON cc.customer_id = o.customer_id
    WHERE o.status IN ('completed', 'pending')
),
activity AS (
    SELECT DISTINCT
        customer_id,
        cohort_month,
        order_month,
        -- months since first purchase, computed from YYYY-MM strings
        (CAST(strftime('%Y', order_month || '-01') AS INT) * 12 + CAST(strftime('%m', order_month || '-01') AS INT))
        - (CAST(strftime('%Y', cohort_month || '-01') AS INT) * 12 + CAST(strftime('%m', cohort_month || '-01') AS INT))
        AS month_index
    FROM orders_flagged
),
cohort_size AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_customers
    FROM customer_cohorts
    GROUP BY cohort_month
)
SELECT
    a.cohort_month,
    a.month_index,
    COUNT(DISTINCT a.customer_id) AS active_customers,
    cs.cohort_customers,
    ROUND(100.0 * COUNT(DISTINCT a.customer_id) / cs.cohort_customers, 1) AS retention_pct
FROM activity a
JOIN cohort_size cs ON cs.cohort_month = a.cohort_month
GROUP BY a.cohort_month, a.month_index
ORDER BY a.cohort_month, a.month_index;


-- ============================================================
-- 3. Churned vs repeat customers
--    repeat  = placed 2+ orders
--    churned = single order and last order > 90 days before the
--              most recent order date in the whole dataset
-- ============================================================
WITH customer_orders AS (
    SELECT
        customer_id,
        COUNT(DISTINCT order_id) AS num_orders,
        MAX(order_date) AS last_order_date
    FROM orders
    WHERE status IN ('completed', 'pending')
    GROUP BY customer_id
),
dataset_max_date AS (
    SELECT MAX(order_date) AS max_date FROM orders WHERE status IN ('completed', 'pending')
)
SELECT
    co.customer_id,
    co.num_orders,
    co.last_order_date,
    CASE
        WHEN co.num_orders >= 2 THEN 'repeat'
        WHEN julianday(dm.max_date) - julianday(co.last_order_date) > 90 THEN 'churned'
        ELSE 'new_single_order'
    END AS customer_status
FROM customer_orders co
CROSS JOIN dataset_max_date dm
ORDER BY co.num_orders DESC;


-- ============================================================
-- 4. Customer segmentation: frequency tier + spend tier + RFM
-- ============================================================
WITH customer_orders AS (
    SELECT
        o.customer_id,
        COUNT(DISTINCT o.order_id) AS frequency,
        MAX(o.order_date) AS last_order_date,
        SUM(oi.quantity * oi.unit_price) AS monetary
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status IN ('completed', 'pending')
    GROUP BY o.customer_id
),
dataset_max_date AS (
    SELECT MAX(order_date) AS max_date FROM orders WHERE status IN ('completed', 'pending')
),
rfm_base AS (
    SELECT
        co.customer_id,
        CAST(julianday(dm.max_date) - julianday(co.last_order_date) AS INT) AS recency_days,
        co.frequency,
        ROUND(co.monetary, 2) AS monetary
    FROM customer_orders co
    CROSS JOIN dataset_max_date dm
),
rfm_scored AS (
    SELECT
        customer_id,
        recency_days,
        frequency,
        monetary,
        NTILE(4) OVER (ORDER BY recency_days DESC) AS r_score,   -- more recent = higher score
        NTILE(4) OVER (ORDER BY frequency ASC)      AS f_score,
        NTILE(4) OVER (ORDER BY monetary ASC)        AS m_score
    FROM rfm_base
)
SELECT
    customer_id,
    recency_days,
    frequency,
    monetary,
    CASE
        WHEN frequency = 1 THEN 'one-time'
        WHEN frequency BETWEEN 2 AND 4 THEN 'occasional'
        ELSE 'loyal'
    END AS frequency_segment,
    CASE
        WHEN monetary < 100 THEN 'low'
        WHEN monetary < 500 THEN 'medium'
        ELSE 'high'
    END AS spend_tier,
    r_score, f_score, m_score,
    (r_score + f_score + m_score) AS rfm_total_score
FROM rfm_scored
ORDER BY rfm_total_score DESC;
