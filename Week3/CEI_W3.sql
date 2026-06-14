use cei_w3;
show tables;
CREATE TABLE superstore_raw (
    `Row ID` INT,
    `Order ID` VARCHAR(20),
    `Order Date` DATE,
    `Ship Date` DATE,
    `Ship Mode` VARCHAR(30),

    `Customer ID` VARCHAR(10),
    `Customer Name` VARCHAR(100),
    `Segment` VARCHAR(30),

    `Country` VARCHAR(50),
    `City` VARCHAR(100),
    `State` VARCHAR(100),
    `Postal Code` INT,
    `Region` VARCHAR(20),

    `Product ID` VARCHAR(20),
    `Category` VARCHAR(30),
    `Sub-Category` VARCHAR(50),
    `Product Name` VARCHAR(255),

    `Sales` DECIMAL(10,4),
    `Quantity` INT,
    `Discount` DECIMAL(4,2),
    `Profit` DECIMAL(12,4)
);
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/Sample - Superstore.csv'
INTO TABLE superstore_raw
CHARACTER SET latin1
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(
`Row ID`,
`Order ID`,
@order_date,
@ship_date,
`Ship Mode`,
`Customer ID`,
`Customer Name`,
`Segment`,
`Country`,
`City`,
`State`,
`Postal Code`,
`Region`,
`Product ID`,
`Category`,
`Sub-Category`,
`Product Name`,
`Sales`,
`Quantity`,
`Discount`,
`Profit`
)
SET
`Order Date` = CASE
    WHEN @order_date LIKE '%/%'
    THEN STR_TO_DATE(@order_date,'%m/%d/%Y')
    ELSE STR_TO_DATE(@order_date,'%m-%d-%Y')
END,
`Ship Date` = CASE
    WHEN @ship_date LIKE '%/%'
    THEN STR_TO_DATE(@ship_date,'%m/%d/%Y')
    ELSE STR_TO_DATE(@ship_date,'%m-%d-%Y')
END;

CREATE TABLE customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    customer_name VARCHAR(100),
    segment VARCHAR(50)
);
INSERT INTO customers (customer_id, customer_name, segment)
SELECT DISTINCT
    `Customer ID`,
    `Customer Name`,
    `Segment`
FROM superstore_raw;
CREATE TABLE products (
    product_id VARCHAR(20) PRIMARY KEY,
    category VARCHAR(30) NOT NULL,
    sub_category VARCHAR(50) NOT NULL,
    product_name VARCHAR(255) NOT NULL
);

INSERT INTO products
SELECT
    `Product ID`,
    MAX(`Category`),
    MAX(`Sub-Category`),
    MAX(`Product Name`)
FROM superstore_raw
GROUP BY `Product ID`;
SELECT DISTINCT
    `Product ID`,
    `Category`,
    `Sub-Category`,
    `Product Name`
FROM superstore_raw;
CREATE TABLE orders (
    row_id INT PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    order_date DATE NOT NULL,
    ship_date DATE NOT NULL,
    ship_mode VARCHAR(20) NOT NULL,

    customer_id VARCHAR(10) NOT NULL,
    product_id VARCHAR(20) NOT NULL,

    country VARCHAR(50) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(50) NOT NULL,
    postal_code INT,
    region VARCHAR(20) NOT NULL,

    sales DECIMAL(10,4) NOT NULL,
    quantity TINYINT UNSIGNED NOT NULL,
    discount DECIMAL(4,2) NOT NULL,
    profit DECIMAL(12,4) NOT NULL,

    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),

    CONSTRAINT fk_orders_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
);
INSERT INTO orders (
    row_id,
    order_id,
    order_date,
    ship_date,
    ship_mode,
    customer_id,
    product_id,
    country,
    city,
    state,
    postal_code,
    region,
    sales,
    quantity,
    discount,
    profit
)
SELECT DISTINCT
    `Row ID`,
    `Order ID`,
    `Order Date`,
    `Ship Date`,
    `Ship Mode`,
    `Customer ID`,
    `Product ID`,
    `Country`,
    `City`,
    `State`,
    `Postal Code`,
    `Region`,
    `Sales`,
    `Quantity`,
    `Discount`,
    `Profit`
FROM superstore_raw;