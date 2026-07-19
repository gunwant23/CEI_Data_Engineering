# CEI_Data_Engineering
# Assignment 1 — E-Commerce Product Data Analysis
A data cleaning and exploration pipeline for an e-commerce product dataset (`Combined_dataset.csv`) using Python and pandas. 
## Workflow
 
### 1. Data Loading & Exploration
- Loads `Combined_dataset.csv` into a pandas DataFrame
- Inspects shape, head/tail, data types (`df.info()`), and summary statistics (`df.describe()`)
- Cleans the `final_price` column by stripping currency symbols (₹) and commas, then casting to integer
- Prints the top 10 product categories by frequency
### 2. Missing Values Handling
- Audits all columns for null counts and percentages
- **Drops** `videos` (78.1% missing) and `what_customers_said` (57.3% missing + unstructured JSON)
- **Fills** `seller_name`, `seller_information`, and `variations` with sensible defaults
- **Fills** `discount` nulls with `0` (undefined discount = no discount in business logic)
### 3. Filtering & Aggregation
- Filters high-rated products (rating ≥ 4.0)
- Identifies budget products (price below dataset average)
- Finds best deals (rating ≥ 4.0 **and** discount ≥ 50%)
- Supports interactive user-input filtering by category and price range
### 4. Duplicate Removal
- Checks for exact duplicate rows and duplicate `product_id` entries
- Drops duplicates, keeping the first occurrence
### 5. Derived Columns & Data Quality Fixes
- Creates a `price_tier` column (Budget / Mid-Range / Premium / Luxury) using mean-based bin cuts
- Detects and corrects inconsistent rows where `final_price ≥ initial_price` despite a non-zero discount
- Computes `savings_amount` per product and total savings across the dataset
### 6. Export
- Saves the cleaned DataFrame to `processed_products.csv`
 
| File | Description |
|---|---|
| `processed_products.csv` | Fully cleaned and enriched product dataset |
