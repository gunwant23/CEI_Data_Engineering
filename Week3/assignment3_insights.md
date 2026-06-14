# Customer Insights & Query Results

Analysis of the Superstore retail dataset (`ord.csv`, `cust.csv`), loaded per the schema defined in `CEI_W3.sql`.

## Dataset Overview

| Metric | Value |
|---|---|
| Order line items | 9,994 |
| Unique orders | 5,009 |
| Unique customers | 793 |
| Unique products | 1,862 |
| Date range | 2014-01-03 to 2017-12-30 |
| Regions | South, West, Central, East |
| Customer segments | Consumer, Corporate, Home Office |

## Headline Metrics

| Metric | Value |
|---|---|
| Total Sales | 2,297,200.86 |
| Total Profit | 286,397.02 |
| Total Quantity Sold | 37,873 units |
| Avg Sales per Order | 458.61 |
| Avg Sales per Line Item | 229.86 |

## Key Insights

### 1. Segment Performance

| Segment | Customers | Sales | Profit |
|---|---|---|---|
| Consumer | 409 | 1,161,401.34 | 134,119.21 |
| Corporate | 236 | 706,146.37 | 91,979.13 |
| Home Office | 148 | 429,653.15 | 60,298.68 |

Consumer drives the most revenue and profit, roughly 1.6x Corporate's profit.

### 2. Region Performance

| Region | Sales | Profit |
|---|---|---|
| West | 725,457.82 | 108,418.45 |
| East | 678,781.24 | 91,522.78 |
| Central | 501,239.89 | 39,706.36 |
| South | 391,721.90 | 46,749.43 |

West leads in both sales and profit. Central has the second-highest sales but the lowest profit, signaling margin issues.

### 3. Product Category Performance

Categories derived from product ID prefixes (FUR = Furniture, OFF = Office Supplies, TEC = Technology).

| Category | Sales | Profit | Profit Margin | Avg Discount |
|---|---|---|---|---|
| Technology | 836,154.03 | 145,454.95 | 17.40% | 13.23% |
| Office Supplies | 719,047.03 | 122,490.80 | 17.04% | 15.73% |
| Furniture | 741,999.80 | 18,451.27 | 2.49% | 17.39% |

Furniture has comparable sales to Technology but only a ~2.5% profit margin — the highest average discount of any category is eroding returns.

### 4. Loss-Making Orders

- **1,871 of 9,994 line items (18.7%) are unprofitable**
- These represent **468,707.15** in sales but a combined **net loss of 156,131.29**

This is a significant margin leakage area.

### 5. Top 5 Customers by Sales

| Rank | Customer | Sales |
|---|---|---|
| 1 | Sean Miller (SM-20320) | 25,043.05 |
| 2 | Tamara Chand (TC-20980) | 19,052.22 |
| 3 | Raymond Buch (RB-19360) | 15,117.34 |
| 4 | Tom Ashbrook (TA-21385) | 14,595.62 |
| 5 | Adrian Barton (AB-10105) | 14,473.57 |

### 6. Top 5 Loss-Making Customers by Profit

| Rank | Customer | Net Profit |
|---|---|---|
| 1 | Cindy Stewart (CS-12505) | -6,626.39 |
| 2 | Grant Thornton (GT-14635) | -4,108.66 |
| 3 | Luke Foster (LF-17185) | -3,583.98 |
| 4 | Sharelle Roach (SR-20425) | -3,333.91 |
| 5 | Henry Goldwyn (HG-14965) | -2,797.96 |

### 7. Repeat Purchase Behavior

- **781 of 793 customers (98.5%)** placed more than one order, indicating strong repeat engagement.

### 8. Yearly Trend

| Year | Sales | Profit |
|---|---|---|
| 2014 | 484,247.50 | 49,543.97 |
| 2015 | 470,532.51 | 61,618.60 |
| 2016 | 609,205.60 | 81,795.17 |
| 2017 | 733,215.26 | 93,439.27 |

Sales and profit both grew steadily from 2015 to 2017, with 2017 the strongest year on record.

### 9. Shipping Mode Distribution

| Ship Mode | Orders | % of Total |
|---|---|---|
| Standard Class | 5,968 | 59.7% |
| Second Class | 1,945 | 19.5% |
| First Class | 1,538 | 15.4% |
| Same Day | 543 | 5.4% |

### 10. Top 5 States by Sales

| Rank | State | Sales |
|---|---|---|
| 1 | California | 457,687.63 |
| 2 | New York | 310,876.27 |
| 3 | Texas | 170,188.05 |
| 4 | Washington | 138,641.27 |
| 5 | Pennsylvania | 116,511.91 |

## Recommendations

- **Audit Furniture discounting** — it generates ~32% of total sales but only ~6% of total profit due to the highest average discount rate.
- **Review Central region discount policy** — sales are 2nd highest but profit ranks lowest among regions.
- **Flag top 5 loss-making customers** for account-level discount/pricing review.
- **Leverage the 98.5% repeat-purchase rate** with loyalty/upsell campaigns focused on Consumer segment and Technology products, which already drive the strongest margins.
