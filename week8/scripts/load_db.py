"""
load_db.py
----------
Creates the SQLite database (data/ecommerce.db) using sql/schema.sql,
loads the cleaned CSVs into it, and verifies row counts / relationships.

Run:
    python load_db.py
"""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CLEAN_DIR = ROOT / "data" / "cleaned"
SCHEMA_PATH = ROOT / "sql" / "schema.sql"
DB_PATH = ROOT / "data" / "ecommerce.db"


def main():
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")

    # Build schema
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())

    # Load cleaned CSVs in FK-safe order: customers -> products -> orders -> order_items
    customers = pd.read_csv(CLEAN_DIR / "customers_clean.csv")
    products = pd.read_csv(CLEAN_DIR / "products_clean.csv")
    orders = pd.read_csv(CLEAN_DIR / "orders_clean.csv")
    order_items = pd.read_csv(CLEAN_DIR / "order_items_clean.csv")

    customers.to_sql("customers", conn, if_exists="append", index=False)
    products.to_sql("products", conn, if_exists="append", index=False)
    orders.to_sql("orders", conn, if_exists="append", index=False)
    order_items.to_sql("order_items", conn, if_exists="append", index=False)

    conn.commit()

    # Verify
    print("=" * 60)
    print("DATABASE LOAD VERIFICATION")
    print("=" * 60)
    for table, df in [
        ("customers", customers),
        ("products", products),
        ("orders", orders),
        ("order_items", order_items),
    ]:
        db_count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        match = "OK" if db_count == len(df) else "MISMATCH"
        print(f"  {table:15s} csv={len(df):6d}  db={db_count:6d}  [{match}]")

    # Referential integrity spot-check
    orphan_orders = conn.execute(
        """SELECT COUNT(*) FROM orders o
           LEFT JOIN customers c ON o.customer_id = c.customer_id
           WHERE c.customer_id IS NULL"""
    ).fetchone()[0]
    orphan_items_order = conn.execute(
        """SELECT COUNT(*) FROM order_items oi
           LEFT JOIN orders o ON oi.order_id = o.order_id
           WHERE o.order_id IS NULL"""
    ).fetchone()[0]
    orphan_items_product = conn.execute(
        """SELECT COUNT(*) FROM order_items oi
           LEFT JOIN products p ON oi.product_id = p.product_id
           WHERE p.product_id IS NULL"""
    ).fetchone()[0]

    print("\nReferential integrity check (should all be 0):")
    print(f"  orders with missing customer      : {orphan_orders}")
    print(f"  order_items with missing order    : {orphan_items_order}")
    print(f"  order_items with missing product  : {orphan_items_product}")

    conn.close()
    print(f"\nDatabase written to: {DB_PATH}")


if __name__ == "__main__":
    main()
