"""
generate_data.py
-----------------
Generates synthetic e-commerce datasets (customers, products, orders, order_items)
using Faker, and intentionally injects realistic data-quality problems so the
cleaning step (clean_data.py) has real work to do.

Intentional inconsistencies injected:
  - customers:  duplicate rows, null emails, mixed-case/whitespace-padded emails
  - products:   null category, negative price, duplicate product rows
  - orders:     invalid/future dates, null customer_id, orders referencing
                customer_ids that don't exist in customers.csv
  - order_items: rows referencing order_ids / product_ids that don't exist,
                 zero/negative quantities, null unit_price

Run:
    python generate_data.py --seed 42 --customers 500 --products 150 --orders 3000
Outputs CSVs to ../data/raw/
"""

import argparse
import random
import string
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

CATEGORIES = [
    "Electronics", "Home & Kitchen", "Clothing", "Books", "Toys",
    "Sports & Outdoors", "Beauty", "Grocery", "Office Supplies", "Automotive",
]

SEGMENTS = ["regular", "vip", "wholesale"]


def gen_customers(fake: Faker, n: int) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        email = fake.email()
        # inject messy email formatting for ~8% of rows
        if random.random() < 0.08:
            email = f"  {email.upper()} "
        # inject null email for ~4%
        if random.random() < 0.04:
            email = None
        rows.append({
            "customer_id": i,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": email,
            "signup_date": fake.date_between(start_date="-3y", end_date="today"),
            "segment": random.choice(SEGMENTS),
            "country": fake.country(),
        })

    df = pd.DataFrame(rows)

    # inject duplicate customer rows (~3%)
    dup_count = max(1, int(n * 0.03))
    dupes = df.sample(dup_count, random_state=random.randint(0, 9999)).copy()
    df = pd.concat([df, dupes], ignore_index=True)

    return df


def gen_products(fake: Faker, n: int) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        category = random.choice(CATEGORIES)
        # inject null category for ~5%
        if random.random() < 0.05:
            category = None
        price = round(random.uniform(3, 500), 2)
        # inject negative/bad price for ~3%
        if random.random() < 0.03:
            price = -abs(price)
        rows.append({
            "product_id": i,
            "product_name": fake.catch_phrase(),
            "category": category,
            "unit_price": price,
            "brand": fake.company(),
        })

    df = pd.DataFrame(rows)

    # inject duplicate product rows (~2%)
    dup_count = max(1, int(n * 0.02))
    dupes = df.sample(dup_count, random_state=random.randint(0, 9999)).copy()
    df = pd.concat([df, dupes], ignore_index=True)

    return df


def gen_orders(fake: Faker, n: int, num_customers: int) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        cust_id = random.randint(1, num_customers)

        # ~4% orders reference a customer_id that does not exist (referential break)
        if random.random() < 0.04:
            cust_id = num_customers + random.randint(1, 50)

        # ~2% orders have null customer_id
        if random.random() < 0.02:
            cust_id = None

        order_date = fake.date_time_between(start_date="-2y", end_date="now")

        # ~2% invalid/future dates
        if random.random() < 0.02:
            order_date = datetime.now() + timedelta(days=random.randint(30, 400))

        status = random.choices(
            ["completed", "completed", "completed", "cancelled", "pending", "refunded"],
            k=1,
        )[0]

        rows.append({
            "order_id": i,
            "customer_id": cust_id,
            "order_date": order_date,
            "status": status,
        })
    return pd.DataFrame(rows)


def gen_order_items(n_items: int, num_orders: int, num_products: int) -> pd.DataFrame:
    rows = []
    item_id = 1
    for order_id in range(1, num_orders + 1):
        # each order has 1-5 line items
        for _ in range(random.randint(1, 5)):
            product_id = random.randint(1, num_products)

            # ~3% reference nonexistent product_id
            if random.random() < 0.03:
                product_id = num_products + random.randint(1, 30)

            quantity = random.randint(1, 6)
            # ~2% invalid quantity
            if random.random() < 0.02:
                quantity = random.choice([0, -1, -3])

            unit_price = round(random.uniform(3, 500), 2)
            # ~3% null price (should be looked up from products during cleaning)
            if random.random() < 0.03:
                unit_price = None

            this_order_id = order_id
            # ~2% reference nonexistent order_id (orphan order_items)
            if random.random() < 0.02:
                this_order_id = num_orders + random.randint(1, 50)

            rows.append({
                "order_item_id": item_id,
                "order_id": this_order_id,
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price,
            })
            item_id += 1
            if item_id > n_items:
                return pd.DataFrame(rows)
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic e-commerce CSV datasets.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--customers", type=int, default=500)
    parser.add_argument("--products", type=int, default=150)
    parser.add_argument("--orders", type=int, default=3000)
    parser.add_argument("--max_items", type=int, default=9000)
    args = parser.parse_args()

    random.seed(args.seed)
    fake = Faker()
    Faker.seed(args.seed)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    customers = gen_customers(fake, args.customers)
    products = gen_products(fake, args.products)
    orders = gen_orders(fake, args.orders, args.customers)
    order_items = gen_order_items(args.max_items, args.orders, args.products)

    customers.to_csv(OUT_DIR / "customers.csv", index=False)
    products.to_csv(OUT_DIR / "products.csv", index=False)
    orders.to_csv(OUT_DIR / "orders.csv", index=False)
    order_items.to_csv(OUT_DIR / "order_items.csv", index=False)

    print("Generated raw datasets:")
    print(f"  customers.csv    -> {len(customers)} rows")
    print(f"  products.csv     -> {len(products)} rows")
    print(f"  orders.csv       -> {len(orders)} rows")
    print(f"  order_items.csv  -> {len(order_items)} rows")
    print(f"Saved to: {OUT_DIR}")


if __name__ == "__main__":
    main()
