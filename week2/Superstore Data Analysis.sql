
-- MAGIC ## 1. Data Exploration

select * from superstore
limit 5;

SELECT COUNT(*) AS total_rows,COUNT(*) AS total_columns
FROM superstore

SELECT 
    COUNT(DISTINCT `Row ID`) AS row_cnt,
    COUNT(DISTINCT `Order ID`) AS ord_cnt,
    COUNT(*) AS total_cnt 
FROM superstore;
--So We can conclude that Row ID is unique and can be used for primary key 
-- First, make Row ID column NOT NULL
ALTER TABLE superstore ALTER COLUMN `Row ID` SET NOT NULL;

-- Then add the primary key constraint
--ALTER TABLE superstore ADD PRIMARY KEY (`Row ID`)

show create table superstore 



-- COMMAND ----------

-- DBTITLE 1,SQL Note
-- MAGIC %md
-- MAGIC **Note:** In SQL, backticks (`) are used for column/table names, while single quotes (') are used for string literals.


-- DBTITLE 1,Data Quality Header
-- MAGIC ## 2. Data Quality

SELECT COUNT(*)
FROM superstore
WHERE Sales IS NULL;

-- MAGIC %md
-- MAGIC ### Challenge 1
-- MAGIC Find all Technology products sold in the West region.
-- MAGIC
-- MAGIC ### Challenge 2
-- MAGIC Find orders where sales are high but profit is negative. Why does this happen?
-- MAGIC
-- MAGIC ### Challenge 3
-- MAGIC Find customers from a specific state who purchased Furniture.
-- MAGIC
-- MAGIC ### Challenge 4
-- MAGIC Find products that received discounts above a chosen percentage.
-- MAGIC
-- MAGIC ### Challenge 5
-- MAGIC Find all orders placed during a holiday season (choose your own date range).

select distinct `Product Name` from superstore 
where Region= 'West' and Category='Technology';

SELECT * 
FROM superstore 
WHERE Sales > (SELECT AVG(Sales) FROM superstore) 
  AND Profit < 0;

SELECT DISTINCT `Customer Name`
FROM superstore
WHERE State = 'Florida' AND Category = 'Furniture';

SELECT * 
FROM superstore 
WHERE `Order Date` BETWEEN '2017-01-01' AND '2017-01-31';


SELECT * 
FROM superstore 
WHERE `Discount` > 0.25;


-- MAGIC ## 4. Advanced Analytics

-- Monthly trends
SELECT 
  YEAR(`Order Date`) AS order_year,
  MONTH(`Order Date`) AS order_month,
  COUNT(*) AS order_count,
  SUM(Sales) AS total_sales
FROM superstore
GROUP BY YEAR(`Order Date`), MONTH(`Order Date`)
ORDER BY order_year, order_month;



-- Top customers by total sales
SELECT 
  `Customer Name`,
  SUM(Sales) AS total_sales
FROM superstore
GROUP BY `Customer Name`
ORDER BY total_sales DESC
LIMIT 10;

-- Find duplicate orders (same Order ID appearing more than once)
SELECT 
  `Order ID`,
  COUNT(*) AS duplicate_count
FROM superstore
GROUP BY `Order ID`
HAVING COUNT(*) > 1;
-- Data Quality Check: Count total rows and null values in Sales column
SELECT COUNT(*) AS row_count FROM superstore;
SELECT COUNT(*) - COUNT(Sales) AS null_sales FROM superstore;