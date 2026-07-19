"""
clean_data.py
-------------
Loads the raw CSVs, cleans them with pandas, validates referential integrity
across tables, and writes cleaned CSVs to data/cleaned/.

Cleaning rules:
  customers:
    - strip/lower-case emails, drop exact duplicate rows
    - drop rows with null email (can't reliably dedupe/contact them)
    - parse signup_date to datetime

  products:
    - drop exact duplicate rows
    - drop rows with negative price
    - fill null category with "Unknown"

  orders:
    - drop rows with null customer_id
    - drop rows whose customer_id does not exist in cleaned customers
    - drop rows with order_date in the future (invalid)
    - parse order_date to datetime

  order_items:
    - drop rows whose order_id does not exist in cleaned orders
    - drop rows whose product_id does not exist in cleaned products
    - drop rows with quantity <= 0
    - fill null unit_price by looking up the product's unit_price

A summary report of rows dropped/fixed at each step is printed to stdout.

Run:
    python clean_data.py
Reads from ../data/raw/, writes to ../data/cleaned/
"""

from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
CLEAN_DIR = Path(__file__).resolve().parent.parent / "data" / "cleaned"


def log(msg: str):
    print(f"  - {msg}")


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    print("\n[customers]")
    start = len(df)

    df["email"] = df["email"].astype("string").str.strip().str.lower()

    before = len(df)
    df = df.dropna(subset=["email"])
    log(f"dropped {before - len(df)} rows with null email")

    before = len(df)
    df = df.drop_duplicates()
    log(f"dropped {before - len(df)} exact duplicate rows")

    before = len(df)
    df = df.drop_duplicates(subset=["customer_id"], keep="first")
    log(f"dropped {before - len(df)} duplicate customer_id rows (kept first)")

    df["signup_date"] = pd.to_datetime(df["signup_date"], errors="coerce")
    before = len(df)
    df = df.dropna(subset=["signup_date"])
    log(f"dropped {before - len(df)} rows with unparseable signup_date")

    print(f"  total: {start} -> {len(df)} rows")
    return df.reset_index(drop=True)


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    print("\n[products]")
    start = len(df)

    before = len(df)
    df = df.drop_duplicates()
    log(f"dropped {before - len(df)} exact duplicate rows")

    before = len(df)
    df = df.drop_duplicates(subset=["product_id"], keep="first")
    log(f"dropped {before - len(df)} duplicate product_id rows (kept first)")

    before = len(df)
    df = df[df["unit_price"] > 0]
    log(f"dropped {before - len(df)} rows with non-positive unit_price")

    n_null_cat = df["category"].isna().sum()
    df["category"] = df["category"].fillna("Unknown")
    log(f"filled {n_null_cat} null categories with 'Unknown'")

    print(f"  total: {start} -> {len(df)} rows")
    return df.reset_index(drop=True)


def clean_orders(df: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    print("\n[orders]")
    start = len(df)

    before = len(df)
    df = df.dropna(subset=["customer_id"])
    log(f"dropped {before - len(df)} rows with null customer_id")

    df["customer_id"] = df["customer_id"].astype(int)
    before = len(df)
    df = df[df["customer_id"].isin(customers["customer_id"])]
    log(f"dropped {before - len(df)} rows with customer_id not in customers table (orphans)")

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    before = len(df)
    df = df.dropna(subset=["order_date"])
    log(f"dropped {before - len(df)} rows with unparseable order_date")

    before = len(df)
    now = pd.Timestamp.now()
    df = df[df["order_date"] <= now]
    log(f"dropped {before - len(df)} rows with future order_date")

    before = len(df)
    df = df.drop_duplicates(subset=["order_id"], keep="first")
    log(f"dropped {before - len(df)} duplicate order_id rows")

    print(f"  total: {start} -> {len(df)} rows")
    return df.reset_index(drop=True)


def clean_order_items(df: pd.DataFrame, orders: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    print("\n[order_items]")
    start = len(df)

    before = len(df)
    df = df[df["order_id"].isin(orders["order_id"])]
    log(f"dropped {before - len(df)} rows with order_id not in orders table (orphans)")

    before = len(df)
    df = df[df["product_id"].isin(products["product_id"])]
    log(f"dropped {before - len(df)} rows with product_id not in products table (orphans)")

    before = len(df)
    df = df[df["quantity"] > 0]
    log(f"dropped {before - len(df)} rows with non-positive quantity")

    # fill missing unit_price from the products table
    n_null_price = df["unit_price"].isna().sum()
    price_lookup = products.set_index("product_id")["unit_price"]
    df["unit_price"] = df["unit_price"].fillna(df["product_id"].map(price_lookup))
    log(f"filled {n_null_price} null unit_price values from products table")

    before = len(df)
    df = df.dropna(subset=["unit_price"])
    log(f"dropped {before - len(df)} rows still missing unit_price after lookup")

    before = len(df)
    df = df.drop_duplicates(subset=["order_item_id"], keep="first")
    log(f"dropped {before - len(df)} duplicate order_item_id rows")

    print(f"  total: {start} -> {len(df)} rows")
    return df.reset_index(drop=True)


def main():
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    customers_raw = pd.read_csv(RAW_DIR / "customers.csv")
    products_raw = pd.read_csv(RAW_DIR / "products.csv")
    orders_raw = pd.read_csv(RAW_DIR / "orders.csv")
    order_items_raw = pd.read_csv(RAW_DIR / "order_items.csv")

    print("=" * 60)
    print("DATA CLEANING REPORT")
    print("=" * 60)

    customers = clean_customers(customers_raw)
    products = clean_products(products_raw)
    orders = clean_orders(orders_raw, customers)
    order_items = clean_order_items(order_items_raw, orders, products)

    customers.to_csv(CLEAN_DIR / "customers_clean.csv", index=False)
    products.to_csv(CLEAN_DIR / "products_clean.csv", index=False)
    orders.to_csv(CLEAN_DIR / "orders_clean.csv", index=False)
    order_items.to_csv(CLEAN_DIR / "order_items_clean.csv", index=False)

    print("\n" + "=" * 60)
    print("FINAL ROW COUNTS")
    print("=" * 60)
    print(f"  customers_clean.csv    : {len(customers)}")
    print(f"  products_clean.csv     : {len(products)}")
    print(f"  orders_clean.csv       : {len(orders)}")
    print(f"  order_items_clean.csv  : {len(order_items)}")
    print(f"\nSaved to: {CLEAN_DIR}")


if __name__ == "__main__":
    main()
