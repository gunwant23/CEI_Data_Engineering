


-- Find all orders where sales are greater than the average sales. (Subquery)  
select * from orders where sales > (select avg(sales) from orders);
-- Find the highest sales order for each customer. (Subquery)  
SELECT order_id,sales as Max_sales FROM orders o
WHERE sales = (
    SELECT MAX(sales) FROM orders WHERE customer_id = o.customer_id
);
-- Calculate total sales for each customer. (CTE)  
WITH customersales as (
select customer_id,Sum(sales) as totalSales from orders group by customer_id ) 
Select * from customersales;
-- Find customers whose total sales are above average. (CTE + Subquery)  
WITH CustomerSales AS
(SELECT customer_id,SUM(sales) AS TotalSales
    FROM orders GROUP BY customer_id
)
SELECT customer_id, TotalSales
FROM CustomerSales
WHERE TotalSales >
(SELECT AVG(TotalSales)FROM CustomerSales);
-- Rank all customers based on total sales (Window Function)
WITH CustomerSales AS (SELECT customer_id,SUM(sales) AS TotalSales FROM orders GROUP BY customer_id
)
SELECT customer_id,TotalSales,RANK() OVER (ORDER BY TotalSales DESC) AS SalesRank
FROM CustomerSales;
-- Assign row numbers to each order within a customer (Window Function + PARTITION BY)
SELECT order_id,customer_id,sales,order_date,
    ROW_NUMBER() OVER(PARTITION BY customer_id ORDER BY order_date) AS OrderNumber
FROM orders;
-- Display top 3 customers based on total sales (Window Function)
WITH CustomerSales AS
(SELECT customer_id,SUM(sales) AS TotalSales FROM orders
    GROUP BY customer_id
)
SELECT
    customer_id,TotalSales
FROM
(select customer_id,TotalSales,
        DENSE_RANK() OVER
        (ORDER BY TotalSales DESC) AS RankNo
    FROM CustomerSales
) T
WHERE RankNo <= 3;

/*Final Combined Query Write one final query that shows: 

Customer Name  

Total Sales  

Rank  

(Use JOIN + CTE + Window Function together) 
*/
WITH CustomerSales AS
(SELECT c.customer_id,c.customer_name,SUM(o.sales) AS TotalSales FROM Customers c
    JOIN Orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_id,c.customer_name)
SELECT customer_name,TotalSales,DENSE_RANK() OVER (ORDER BY TotalSales DESC) AS SalesRank
FROM CustomerSales;

/*Mini Project: Customer Sales Insights 

Answer the following using SQL: */

-- Who are the top 5 customers?  
SELECT  SUM(sales) AS TotalSales,c.customer_name
FROM Orders o join customers c on o.customer_id=c.customer_id
GROUP BY o.customer_id
ORDER BY TotalSales DESC
LIMIT 5;
-- Who are the bottom 5 customers?  
SELECT  SUM(sales) AS TotalSales,c.customer_name
FROM Orders o join customers c on o.customer_id=c.customer_id
GROUP BY o.customer_id
ORDER BY TotalSales
LIMIT 5;
-- Which customers made only one order?  
SELECT c.customer_name
FROM Orders o join customers c on o.customer_id=c.customer_id
GROUP BY o.customer_id
HAVING COUNT(*) = 1;
-- Which customers have above-average sales?  
SELECT customer_id, SUM(sales) AS TotalSales
FROM Orders
GROUP BY customer_id
HAVING SUM(sales) >
(SELECT AVG(TotalSales)
    FROM(SELECT SUM(sales) AS TotalSales FROM Orders GROUP BY customer_id ) t
);
-- What is the highest order value per customer? 
SELECT c.customer_name, SUM(o.sales) AS TotalSales FROM Customers c
JOIN Orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_name
ORDER BY TotalSales DESC
LIMIT 5;


