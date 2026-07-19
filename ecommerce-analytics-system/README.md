# E-Commerce Order Analytics System

An end-to-end analytics pipeline that generates a realistic (and realistically messy) e-commerce
dataset, cleans it with pandas, loads it into a relational database, and answers business
questions with SQL — joins, aggregations, window functions, cohort/retention analysis, and
RFM-style customer segmentation — all exposed through a CLI reporting tool.

## 1. Architecture

```
                 ┌──────────────────┐
                 │ generate_data.py │  Faker + random → intentionally messy CSVs
                 └────────┬─────────┘
                          │  data/raw/*.csv
                          ▼
                 ┌──────────────────┐
                 │  clean_data.py   │  pandas: dedupe, nulls, type fixes,
                 └────────┬─────────┘  referential-integrity validation
                          │  data/cleaned/*.csv
                          ▼
                 ┌──────────────────┐
                 │   load_db.py     │  builds schema.sql, loads cleaned CSVs,
                 └────────┬─────────┘  verifies row counts + FK integrity
                          │  data/ecommerce.db (SQLite)
                          ▼
      ┌──────────────────────────────────────┐
      │        sql/*.sql analytics            │
      │  aggregations · window_functions ·    │
      │  cohort_analysis                      │
      └───────────────────┬────────────────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │  report_cli.py   │  argparse CLI → runs a named report →
                 └──────────────────┘  prints as a table (tabulate) / exports CSV
```

**Why SQLite:** zero setup, single-file database, full support for window functions, CTEs,
and foreign keys — ideal for a self-contained, reviewable project. The same SQL (aside from a
few SQLite-specific date functions like `strftime`/`julianday`) translates directly to
PostgreSQL/MySQL with minor syntax changes.

## 2. Project Layout

```
ecommerce-analytics-system/
│── data/
│   ├── raw/                  # messy, as-generated CSVs
│   ├── cleaned/               # cleaned CSVs (output of clean_data.py)
│   └── ecommerce.db           # SQLite database (output of load_db.py)
│── scripts/
│   ├── generate_data.py       # Step 1: synthetic data generation
│   ├── clean_data.py          # Step 2: pandas cleaning + validation
│   ├── load_db.py             # Step 3: schema creation + data load + verification
│   ├── report_cli.py          # Step 8: CLI reporting tool
│   └── run_pipeline.py        # convenience: runs steps 1-3 in one command
│── sql/
│   ├── schema.sql             # table DDL with PK / FK / NOT NULL / CHECK constraints
│   ├── aggregations.sql       # Step 4: joins & aggregations
│   ├── window_functions.sql   # Step 5: RANK/DENSE_RANK, running totals, moving averages, CTEs
│   └── cohort_analysis.sql    # Step 6 & 7: cohorts, retention, churn, RFM segmentation
│── output/
│   └── sample_reports/        # sample CLI output for every report (.txt)
│── README.md
```

## 3. Data Model

| Table          | Key columns                                           | Notes |
|----------------|--------------------------------------------------------|-------|
| `customers`    | `customer_id` PK, `email` UNIQUE                        | `segment` ∈ {regular, vip, wholesale} |
| `products`     | `product_id` PK                                         | `unit_price > 0` (CHECK) |
| `orders`       | `order_id` PK, `customer_id` FK → customers              | `status` ∈ {completed, pending, cancelled, refunded} |
| `order_items`  | `order_item_id` PK, `order_id` FK, `product_id` FK        | `quantity > 0`, `unit_price > 0` (CHECK) |

Revenue queries filter to `status IN ('completed', 'pending')` so cancelled/refunded orders
don't inflate revenue figures.

## 4. Intentional Data-Quality Issues (and how they're fixed)

`generate_data.py` deliberately injects the kind of mess real e-commerce exports have:

| Table         | Issue injected                                   | Fix in `clean_data.py`                                  |
|---------------|---------------------------------------------------|-----------------------------------------------------------|
| customers     | duplicate rows, null/whitespace/mixed-case emails | drop duplicates, drop null emails, normalize email casing |
| products      | duplicate rows, null category, negative price      | drop duplicates, fill category as "Unknown", drop bad prices |
| orders        | null/orphan `customer_id`, future dates             | drop nulls, drop orphans (anti-join against customers), drop future dates |
| order_items   | orphan `order_id`/`product_id`, bad quantity, null price | drop orphans (anti-join), drop non-positive quantity, backfill price from `products` |

Every cleaning step prints a before/after row count so data loss is auditable, and
`load_db.py` re-verifies referential integrity after loading (should always report 0 orphans).

## 5. Setup

```bash
cd ecommerce-analytics-system
pip install faker pandas tabulate
```

## 6. Running the Pipeline

**Option A — one command:**
```bash
cd scripts
python run_pipeline.py                       # uses defaults (500 customers, 150 products, 3000 orders)
python run_pipeline.py --customers 1000 --products 200 --orders 5000   # custom sizes
```

**Option B — step by step:**
```bash
cd scripts
python generate_data.py --seed 42 --customers 500 --products 150 --orders 3000
python clean_data.py
python load_db.py
```

Each step prints a report of what it did (rows generated, rows dropped/fixed, row-count
verification against the database).

## 7. Using the CLI Reporting Tool

```bash
python report_cli.py --report list
```
```
Available reports:

  revenue_by_customer  - Total revenue per customer
  revenue_by_category  - Total revenue per product category
  revenue_by_month     - Total revenue per month
  top_products         - Top products by quantity sold and revenue
  aov_by_segment       - Average order value (AOV) by customer segment
  top_customers        - Customers ranked by lifetime value
  retention            - Monthly retention rate per first-purchase cohort
  churn                - Repeat vs churned vs new customers
  segmentation         - RFM-style customer segmentation (frequency tier, spend tier)
```

Run any report:
```bash
python report_cli.py --report revenue_by_customer --limit 10
python report_cli.py --report top_products --limit 5
python report_cli.py --report segmentation --limit 20
```

Options:
| Flag       | Description                                              | Default              |
|------------|------------------------------------------------------------|-----------------------|
| `--report` | report name, or `list` to see all options (required)       | —                      |
| `--db`     | path to the SQLite database                                 | `../data/ecommerce.db` |
| `--limit`  | max rows returned (must be a positive integer)               | `20`                   |
| `--format` | any `tabulate` table format (`psql`, `grid`, `github`, ...)  | `psql`                 |
| `--out`    | also write results to a CSV file at this path                | none                   |

Export example:
```bash
python report_cli.py --report top_customers --limit 50 --out ../output/top_50_customers.csv
```

## 8. Sample Output

```
=== Total revenue per customer ===

+---------------+-----------------+-----------+-----------------+--------------+
|   customer_id | customer_name   | segment   |   total_revenue |   num_orders |
|---------------+-----------------+-----------+-----------------+--------------|
|           361 | Julie Phillips  | vip       |         32217.7 |            9 |
|           200 | Bryan Parsons   | regular   |         30099   |           11 |
|           429 | Sara Hart       | wholesale |         29371.5 |           12 |
|           144 | Jeffrey Gilbert | vip       |         27263.6 |           10 |
|           163 | Steve Miller    | regular   |         26238.3 |            9 |
+---------------+-----------------+-----------+-----------------+--------------+

5 row(s) returned.
```

Full sample output for every report is saved under `output/sample_reports/`.

## 9. Edge Case Handling

The CLI and pipeline scripts have been tested against:

- **Unknown report name** → prints an error and the list of valid reports, exits with code 1
  (does not crash).
- **Invalid `--limit`** (zero or negative) → validated and rejected before any query runs.
- **Missing/inaccessible database file** → connection is checked up front with a clear message
  telling the user to run `load_db.py`, instead of a raw traceback.
- **Empty result sets** (e.g. a database with a single customer and zero orders) → every report
  prints `(no rows returned for this report / filter combination)` instead of an empty/blank
  table or an exception.
- **Referential-integrity edge cases** (orphan orders, orphan order_items, orphan customer
  references) → actively generated in the raw data and removed during cleaning; `load_db.py`
  re-verifies zero orphans exist in the final database.
- **Future/invalid dates** → generated intentionally, then filtered out in `clean_data.py`
  before they can distort monthly revenue or cohort calculations.

## 10. SQL Analytics Reference

- `sql/aggregations.sql` — revenue per customer / category / month, top products, AOV by segment.
- `sql/window_functions.sql` — `RANK()`/`DENSE_RANK()` customer LTV leaderboard, running-total
  and 3-month moving-average revenue via `SUM() OVER` / `AVG() OVER`, month-over-month growth
  rate using a CTE + `LAG()`.
- `sql/cohort_analysis.sql` — first-purchase-month cohorts (as a view), monthly retention rate
  per cohort, churned/repeat/new customer classification, and a full RFM (Recency, Frequency,
  Monetary) segmentation using `NTILE(4)`.

## 11. Extending to PostgreSQL / MySQL

The schema and queries use standard ANSI SQL plus a handful of SQLite-specific functions:
`strftime()` and `julianday()` for date math, and `AUTOINCREMENT`-free `INTEGER PRIMARY KEY`.
To port to Postgres: replace `strftime('%Y-%m', col)` with `to_char(col, 'YYYY-MM')`, and
`julianday(a) - julianday(b)` with `a::date - b::date`. `RANK()`, `DENSE_RANK()`, `NTILE()`,
`LAG()`, and windowed `SUM()/AVG()` are all standard and require no changes.
