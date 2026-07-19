#!/usr/bin/env python3
"""
report_cli.py
-------------
Command-line reporting tool for the e-commerce analytics database.

Usage:
    python report_cli.py --report revenue_by_customer
    python report_cli.py --report revenue_by_category
    python report_cli.py --report revenue_by_month
    python report_cli.py --report top_products [--limit 10]
    python report_cli.py --report aov_by_segment
    python report_cli.py --report top_customers [--limit 10]
    python report_cli.py --report retention
    python report_cli.py --report churn
    python report_cli.py --report segmentation
    python report_cli.py --report list          # list all available reports

Options:
    --db PATH       path to the sqlite database (default: ../data/ecommerce.db)
    --limit N       max rows to display for reports that support it (default: 20)
    --format FMT    output table format for tabulate (default: psql)
    --out PATH      also write the report output to a file (e.g. CSV) based on extension
"""

import argparse
import sqlite3
import sys
from pathlib import Path

import pandas as pd
from tabulate import tabulate

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "ecommerce.db"

# ------------------------------------------------------------------
# Report registry: name -> (description, SQL template)
# {limit} is substituted where relevant.
# ------------------------------------------------------------------
REPORTS = {
    "revenue_by_customer": (
        "Total revenue per customer",
        """
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
        ORDER BY total_revenue DESC
        LIMIT {limit};
        """,
    ),
    "revenue_by_category": (
        "Total revenue per product category",
        """
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
        ORDER BY total_revenue DESC
        LIMIT {limit};
        """,
    ),
    "revenue_by_month": (
        "Total revenue per month",
        """
        SELECT
            strftime('%Y-%m', o.order_date) AS order_month,
            ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue,
            COUNT(DISTINCT o.order_id) AS num_orders
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.status IN ('completed', 'pending')
        GROUP BY order_month
        ORDER BY order_month
        LIMIT {limit};
        """,
    ),
    "top_products": (
        "Top products by quantity sold and revenue",
        """
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
        LIMIT {limit};
        """,
    ),
    "aov_by_segment": (
        "Average order value (AOV) by customer segment",
        """
        WITH order_totals AS (
            SELECT o.order_id, o.customer_id, SUM(oi.quantity * oi.unit_price) AS order_total
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
        ORDER BY avg_order_value DESC
        LIMIT {limit};
        """,
    ),
    "top_customers": (
        "Customers ranked by lifetime value",
        """
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
            customer_id, customer_name, segment, lifetime_value,
            RANK() OVER (ORDER BY lifetime_value DESC) AS ltv_rank
        FROM customer_ltv
        ORDER BY ltv_rank
        LIMIT {limit};
        """,
    ),
    "retention": (
        "Monthly retention rate per first-purchase cohort",
        """
        WITH customer_cohorts AS (
            SELECT customer_id, MIN(strftime('%Y-%m', order_date)) AS cohort_month
            FROM orders WHERE status IN ('completed', 'pending')
            GROUP BY customer_id
        ),
        orders_flagged AS (
            SELECT o.customer_id, strftime('%Y-%m', o.order_date) AS order_month, cc.cohort_month
            FROM orders o JOIN customer_cohorts cc ON cc.customer_id = o.customer_id
            WHERE o.status IN ('completed', 'pending')
        ),
        activity AS (
            SELECT DISTINCT customer_id, cohort_month, order_month,
                (CAST(strftime('%Y', order_month || '-01') AS INT) * 12 + CAST(strftime('%m', order_month || '-01') AS INT))
                - (CAST(strftime('%Y', cohort_month || '-01') AS INT) * 12 + CAST(strftime('%m', cohort_month || '-01') AS INT))
                AS month_index
            FROM orders_flagged
        ),
        cohort_size AS (
            SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_customers
            FROM customer_cohorts GROUP BY cohort_month
        )
        SELECT
            a.cohort_month, a.month_index,
            COUNT(DISTINCT a.customer_id) AS active_customers,
            cs.cohort_customers,
            ROUND(100.0 * COUNT(DISTINCT a.customer_id) / cs.cohort_customers, 1) AS retention_pct
        FROM activity a JOIN cohort_size cs ON cs.cohort_month = a.cohort_month
        GROUP BY a.cohort_month, a.month_index
        ORDER BY a.cohort_month, a.month_index
        LIMIT {limit};
        """,
    ),
    "churn": (
        "Repeat vs churned vs new customers",
        """
        WITH customer_orders AS (
            SELECT customer_id, COUNT(DISTINCT order_id) AS num_orders, MAX(order_date) AS last_order_date
            FROM orders WHERE status IN ('completed', 'pending')
            GROUP BY customer_id
        ),
        dataset_max_date AS (
            SELECT MAX(order_date) AS max_date FROM orders WHERE status IN ('completed', 'pending')
        )
        SELECT
            co.customer_id, co.num_orders, co.last_order_date,
            CASE
                WHEN co.num_orders >= 2 THEN 'repeat'
                WHEN julianday(dm.max_date) - julianday(co.last_order_date) > 90 THEN 'churned'
                ELSE 'new_single_order'
            END AS customer_status
        FROM customer_orders co CROSS JOIN dataset_max_date dm
        ORDER BY co.num_orders DESC
        LIMIT {limit};
        """,
    ),
    "segmentation": (
        "RFM-style customer segmentation (frequency tier, spend tier)",
        """
        WITH customer_orders AS (
            SELECT o.customer_id, COUNT(DISTINCT o.order_id) AS frequency,
                   MAX(o.order_date) AS last_order_date,
                   SUM(oi.quantity * oi.unit_price) AS monetary
            FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
            WHERE o.status IN ('completed', 'pending')
            GROUP BY o.customer_id
        ),
        dataset_max_date AS (
            SELECT MAX(order_date) AS max_date FROM orders WHERE status IN ('completed', 'pending')
        ),
        rfm_base AS (
            SELECT co.customer_id,
                   CAST(julianday(dm.max_date) - julianday(co.last_order_date) AS INT) AS recency_days,
                   co.frequency, ROUND(co.monetary, 2) AS monetary
            FROM customer_orders co CROSS JOIN dataset_max_date dm
        ),
        rfm_scored AS (
            SELECT customer_id, recency_days, frequency, monetary,
                   NTILE(4) OVER (ORDER BY recency_days DESC) AS r_score,
                   NTILE(4) OVER (ORDER BY frequency ASC) AS f_score,
                   NTILE(4) OVER (ORDER BY monetary ASC) AS m_score
            FROM rfm_base
        )
        SELECT customer_id, recency_days, frequency, monetary,
            CASE WHEN frequency = 1 THEN 'one-time'
                 WHEN frequency BETWEEN 2 AND 4 THEN 'occasional'
                 ELSE 'loyal' END AS frequency_segment,
            CASE WHEN monetary < 100 THEN 'low'
                 WHEN monetary < 500 THEN 'medium'
                 ELSE 'high' END AS spend_tier,
            r_score, f_score, m_score, (r_score + f_score + m_score) AS rfm_total_score
        FROM rfm_scored
        ORDER BY rfm_total_score DESC
        LIMIT {limit};
        """,
    ),
}


def list_reports():
    print("Available reports:\n")
    for name, (desc, _) in REPORTS.items():
        print(f"  {name:20s} - {desc}")


def connect_db(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        print(f"ERROR: database not found at '{db_path}'.")
        print("Run scripts/load_db.py first to build the database.")
        sys.exit(1)
    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("SELECT 1;")  # sanity ping
        return conn
    except sqlite3.Error as e:
        print(f"ERROR: could not connect to database '{db_path}': {e}")
        sys.exit(1)


def run_report(conn: sqlite3.Connection, name: str, limit: int) -> pd.DataFrame:
    if name not in REPORTS:
        print(f"ERROR: unknown report '{name}'.")
        list_reports()
        sys.exit(1)

    _, sql_template = REPORTS[name]
    sql = sql_template.format(limit=limit)
    try:
        df = pd.read_sql_query(sql, conn)
    except sqlite3.Error as e:
        print(f"ERROR: query failed for report '{name}': {e}")
        sys.exit(1)
    return df


def main():
    parser = argparse.ArgumentParser(
        description="E-commerce analytics CLI reporting tool.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--report", required=True,
        help="Report to run. Use '--report list' to see all options.",
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to SQLite database.")
    parser.add_argument("--limit", type=int, default=20, help="Max rows to display (default: 20).")
    parser.add_argument("--format", default="psql", help="tabulate table format (default: psql).")
    parser.add_argument("--out", type=Path, default=None, help="Optional path to also save output as CSV.")
    args = parser.parse_args()

    if args.report == "list":
        list_reports()
        return

    if args.limit <= 0:
        print("ERROR: --limit must be a positive integer.")
        sys.exit(1)

    conn = connect_db(args.db)
    desc, _ = REPORTS.get(args.report, (None, None))
    if desc is None:
        print(f"ERROR: unknown report '{args.report}'.")
        list_reports()
        sys.exit(1)

    df = run_report(conn, args.report, args.limit)
    conn.close()

    print(f"\n=== {desc} ===\n")
    if df.empty:
        print("(no rows returned for this report / filter combination)")
    else:
        print(tabulate(df, headers="keys", tablefmt=args.format, showindex=False))
        print(f"\n{len(df)} row(s) returned.")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(args.out, index=False)
        print(f"\nSaved output to: {args.out}")


if __name__ == "__main__":
    main()
