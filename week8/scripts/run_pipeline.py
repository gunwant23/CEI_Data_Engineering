#!/usr/bin/env python3
"""
run_pipeline.py
----------------
Convenience wrapper that runs the full pipeline end-to-end:
  1. generate_data.py  (raw CSVs)
  2. clean_data.py     (cleaned CSVs)
  3. load_db.py         (SQLite database)

Run:
    python run_pipeline.py
    python run_pipeline.py --customers 1000 --products 200 --orders 5000
"""

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent


def run(cmd):
    print(f"\n$ {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"Step failed: {' '.join(cmd)}")
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description="Run the full data pipeline end-to-end.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--customers", type=int, default=500)
    parser.add_argument("--products", type=int, default=150)
    parser.add_argument("--orders", type=int, default=3000)
    parser.add_argument("--max_items", type=int, default=9000)
    args = parser.parse_args()

    python = sys.executable

    run([python, str(SCRIPTS_DIR / "generate_data.py"),
         "--seed", str(args.seed),
         "--customers", str(args.customers),
         "--products", str(args.products),
         "--orders", str(args.orders),
         "--max_items", str(args.max_items)])

    run([python, str(SCRIPTS_DIR / "clean_data.py")])
    run([python, str(SCRIPTS_DIR / "load_db.py")])

    print("\nPipeline complete. Try:")
    print("  python report_cli.py --report list")
    print("  python report_cli.py --report revenue_by_customer --limit 10")


if __name__ == "__main__":
    main()
