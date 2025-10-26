# Analyses Specification

Analyses in dbt are SQL queries that don't create persisted tables or views. They are useful for ad-hoc analysis, exploration, and one-time reports. For an e-commerce analytics project on BigQuery, analyses can help answer specific business questions, validate model logic, and provide insights that don't need to be refreshed regularly.

## Purpose of Analyses

1. **Ad-hoc Exploration**: Investigate specific business questions
2. **Model Validation**: Verify that models are working as expected
3. **One-time Reports**: Generate reports that don't need to be refreshed regularly
4. **Documentation**: Demonstrate how to use models for analysis

## Example Analysis Files

### 1. Customer Analysis

#### analyses/customers/customer_cohort_retention.sql

```sql
/*
  Analysis: Customer Cohort Retention
  
  This analysis examines customer retention by cohort (acquisition month).
  It shows what percentage of customers from each cohort continue to place
  orders in subsequent months.
*/

with dim_customers as (
    select * from {{ ref('dim_customers') }}
),

fact_orders as (
    select * from {{ ref('fact_orders') }}
),

-- Create cohorts based on first order month
customer_cohorts as (
    select
        customer_id,
        date_trunc(first_order_date, month) as cohort_month
    from dim_customers
    where first_order_date is not null
),

-- Get all orders with cohort information
cohort_orders as (
    select
        c.customer_id,
        c.cohort_month,
        date_trunc(o.order_date, month) as order_month,
        date_diff(
            date_trunc(o.order_date, month),
            c.cohort_month,
            month
        ) as months_since_first_order
    from customer_cohorts c
    inner join fact_orders o on c.customer_id = o.customer_id
),

-- Count distinct customers by cohort and month
cohort_retention as (
    select
        cohort_month,
        months_since_first_order,
        count(distinct customer_id) as customer_count
    from cohort_orders
    group by 1, 2
),

-- Calculate cohort sizes
cohort_sizes as (
    select
        cohort_month,
        count(distinct customer_id) as cohort_size
    from customer_cohorts
    group by 1
),

-- Calculate retention rates
retention_rates as (
    select
        cr.cohort_month,
        cr.months_since_first_order,
        cr.customer_count,
        cs.cohort_size,
        round(safe_divide(cr.customer_count, cs.cohort_size) * 100, 2) as retention_rate
    from cohort_retention cr
    inner join cohort_sizes cs on cr.cohort_month = cs.cohort_month
    order by 1, 2
)

select * from retention_rates
```

### 2. Product Analysis

#### analyses/products/product_affinity_analysis.sql

```sql
/*
  Analysis: Product Affinity Analysis
  
  This analysis identifies products that are frequently purchased together.
  It can be used for product recommendations and bundle promotions.
*/

with fact_order_items as (
    select * from {{ ref('fact_order_items') }}
),

dim_products as (
    select * from {{ ref('dim_products') }}
),

-- Get all product pairs within the same order
product_pairs as (
    select
        a.order_id,
        a.product_id as product_a_id,
        b.product_id as product_b_id
    from fact_order_items a
    inner join fact_order_items b
        on a.order_id = b.order_id
        and a.product_id < b.product_id  -- Avoid duplicates and self-pairs
),

-- Count occurrences of each product pair
pair_counts as (
    select
        product_a_id,
        product_b_id,
        count(distinct order_id) as order_count
    from product_pairs
    group by 1, 2
),

-- Get individual product order counts
product_counts as (
    select
        product_id,
        count(distinct order_id) as order_count
    from fact_order_items
    group by 1
),

-- Calculate affinity metrics
product_affinity as (
    select
        pc.product_a_id,
        pc.product_b_id,
        pa.product_name as product_a_name,
        pb.product_name as product_b_name,
        pc.order_count as pair_order_count,
        pca.order_count as product_a_order_count,
        pcb.order_count as product_b_order_count,
        round(safe_divide(pc.order_count, pca.order_count) * 100, 2) as pct_a_with_b,
        round(safe_divide(pc.order_count, pcb.order_count) * 100, 2) as pct_b_with_a
    from pair_counts pc
    inner join product_counts pca on pc.product_a_id = pca.product_id
    inner join product_counts pcb on pc.product_b_id = pcb.product_id
    inner join dim_products pa on pc.product_a_id = pa.product_id
    inner join dim_products pb on pc.product_b_id = pb.product_id
    where pc.order_count >= 5  -- Minimum threshold for significance
    order by pc.order_count desc
)

select * from product_affinity
```

### 3. Sales Analysis

#### analyses/sales/sales_forecast.sql

```sql
/*
  Analysis: Sales Forecast
  
  This analysis creates a simple time-series forecast for sales
  using a 30-day moving average and linear regression.
*/

with fact_orders as (
    select * from {{ ref('fact_orders') }}
),

-- Aggregate daily sales
daily_sales as (
    select
        order_date,
        sum(total_amount) as daily_revenue
    from fact_orders
    where is_cancelled = false
    group by 1
),

-- Calculate 30-day moving average
moving_avg as (
    select
        order_date,
        daily_revenue,
        avg(daily_revenue) over (
            order by order_date
            rows between 29 preceding and current row
        ) as revenue_30d_avg
    from daily_sales
),

-- Create date sequence for forecast
date_sequence as (
    select
        date as forecast_date
    from unnest(generate_date_array(
        (select max(order_date) from fact_orders),
        date_add((select max(order_date) from fact_orders), interval 90 day),
        interval 1 day
    )) as date
),

-- Linear regression coefficients (simplified)
-- In a real implementation, you would use BigQuery ML or another method
-- for more sophisticated forecasting
regression_params as (
    select
        avg(daily_revenue) as base_value,
        covar_pop(unix_date(order_date), daily_revenue) / variance(unix_date(order_date)) as slope
    from daily_sales
    where order_date >= date_sub((select max(order_date) from daily_sales), interval 90 day)
),

-- Generate forecast
forecast as (
    select
        ds.forecast_date,
        rp.base_value + rp.slope * (unix_date(ds.forecast_date) - unix_date((select max(order_date) from daily_sales))) as forecasted_revenue
    from date_sequence ds
    cross join regression_params rp
),

-- Combine historical and forecasted data
combined_data as (
    select
        order_date as date,
        daily_revenue as revenue,
        revenue_30d_avg,
        null as forecasted_revenue,
        'Historical' as data_type
    from moving_avg
    
    union all
    
    select
        forecast_date as date,
        null as revenue,
        null as revenue_30d_avg,
        forecasted_revenue,
        'Forecast' as data_type
    from forecast
)

select * from combined_data
order by date
```

### 4. Marketing Analysis

#### analyses/marketing/campaign_roi_comparison.sql

```sql
/*
  Analysis: Campaign ROI Comparison
  
  This analysis compares the ROI of different marketing campaigns
  and identifies the most effective channels and campaign types.
*/

with fact_orders as (
    select * from {{ ref('fact_orders') }}
),

dim_customers as (
    select * from {{ ref('dim_customers') }}
),

stg_marketing_campaigns as (
    select * from {{ ref('stg_marketing_campaigns') }}
),

-- Calculate campaign performance metrics
campaign_performance as (
    select
        c.campaign_id,
        c.name as campaign_name,
        c.type as campaign_type,
        c.start_date,
        c.end_date,
        c.budget,
        count(distinct o.order_id) as order_count,
        count(distinct o.customer_id) as customer_count,
        sum(o.total_amount) as total_revenue,
        sum(o.total_amount) - c.budget as campaign_profit,
        safe_divide(
            sum(o.total_amount) - c.budget,
            c.budget
        ) as roi,
        safe_divide(
            c.budget,
            count(distinct o.customer_id)
        ) as cost_per_customer,
        date_diff(c.end_date, c.start_date, day) as campaign_duration_days
    from stg_marketing_campaigns c
    left join fact_orders o on 
        o.order_date between c.start_date and c.end_date
        and o.campaign_id = c.campaign_id
    group by 1, 2, 3, 4, 5, 6
),

-- Rank campaigns by ROI
ranked_campaigns as (
    select
        *,
        row_number() over (partition by campaign_type order by roi desc) as rank_within_type,
        row_number() over (order by roi desc) as overall_rank
    from campaign_performance
)

select * from ranked_campaigns
order by overall_rank
```

### 5. Inventory Analysis

#### analyses/inventory/stock_out_risk_analysis.sql

```sql
/*
  Analysis: Stock-Out Risk Analysis
  
  This analysis identifies products at risk of stocking out
  based on current inventory levels and historical sales velocity.
*/

with fact_inventory_snapshots as (
    select * from {{ ref('fact_inventory_snapshots') }}
),

fact_order_items as (
    select * from {{ ref('fact_order_items') }}
),

dim_products as (
    select * from {{ ref('dim_products') }}
),

-- Get latest inventory snapshot for each product
current_inventory as (
    select
        product_id,
        sum(quantity_on_hand) as total_quantity
    from fact_inventory_snapshots
    where snapshot_date_id = (select max(snapshot_date_id) from fact_inventory_snapshots)
    group by 1
),

-- Calculate sales velocity (units sold per day) over the last 30 days
sales_velocity as (
    select
        product_id,
        sum(quantity) as units_sold_30d,
        safe_divide(
            sum(quantity),
            30
        ) as daily_sales_velocity
    from fact_order_items
    where order_date >= date_sub(current_date(), interval 30 day)
    group by 1
),

-- Calculate days of inventory remaining and stock-out risk
stock_out_risk as (
    select
        p.product_id,
        p.product_name,
        p.category_name,
        ci.total_quantity as current_inventory,
        sv.units_sold_30d,
        sv.daily_sales_velocity,
        safe_divide(
            ci.total_quantity,
            sv.daily_sales_velocity
        ) as days_of_inventory_remaining,
        case
            when safe_divide(ci.total_quantity, sv.daily_sales_velocity) < 7 then 'High'
            when safe_divide(ci.total_quantity, sv.daily_sales_velocity) < 14 then 'Medium'
            when safe_divide(ci.total_quantity, sv.daily_sales_velocity) < 30 then 'Low'
            else 'None'
        end as stock_out_risk
    from dim_products p
    left join current_inventory ci on p.product_id = ci.product_id
    left join sales_velocity sv on p.product_id = sv.product_id
    where sv.daily_sales_velocity > 0  -- Only include products with recent sales
)

select * from stock_out_risk
order by days_of_inventory_remaining asc
```

## Analysis Best Practices

1. **Documentation**:
   - Include a header comment explaining the purpose of the analysis
   - Document key assumptions and limitations
   - Explain complex calculations and business logic

2. **Organization**:
   - Group analyses by business domain
   - Use consistent naming conventions
   - Structure queries with clear CTEs

3. **Performance**:
   - Optimize queries for large datasets
   - Use appropriate filters to limit data volume
   - Consider query cost and execution time

4. **Reusability**:
   - Reference dbt models using the `ref()` function
   - Avoid hardcoding values
   - Structure analyses to be adaptable for similar questions

5. **Visualization Preparation**:
   - Format output for easy visualization
   - Include calculated metrics for common charts
   - Consider how the data will be consumed

## Analysis Directory Structure

```
analyses/
├── customers/
│   ├── customer_cohort_retention.sql
│   ├── customer_segmentation_analysis.sql
│   └── customer_acquisition_cost.sql
├── products/
│   ├── product_affinity_analysis.sql
│   ├── product_performance_trends.sql
│   └── product_return_rate_analysis.sql
├── sales/
│   ├── sales_forecast.sql
│   ├── sales_by_channel.sql
│   └── order_funnel_analysis.sql
├── marketing/
│   ├── campaign_roi_comparison.sql
│   ├── marketing_channel_effectiveness.sql
│   └── customer_acquisition_by_campaign.sql
└── inventory/
    ├── stock_out_risk_analysis.sql
    ├── inventory_turnover_analysis.sql
    └── warehouse_efficiency_analysis.sql
```

## Analysis Documentation

Create an `analyses/README.md` file to document your analyses:

```markdown
# Analyses

This directory contains ad-hoc analyses that don't create persisted tables or views. These analyses are useful for exploring data, answering specific business questions, and validating model logic.

## Customer Analyses

- `customer_cohort_retention.sql`: Examines customer retention by cohort (acquisition month)
- `customer_segmentation_analysis.sql`: Segments customers based on behavior and value
- `customer_acquisition_cost.sql`: Calculates customer acquisition cost by channel and campaign

## Product Analyses

- `product_affinity_analysis.sql`: Identifies products that are frequently purchased together
- `product_performance_trends.sql`: Analyzes product performance trends over time
- `product_return_rate_analysis.sql`: Examines product return rates and reasons

## Sales Analyses

- `sales_forecast.sql`: Creates a time-series forecast for sales
- `sales_by_channel.sql`: Analyzes sales performance by channel
- `order_funnel_analysis.sql`: Examines the order conversion funnel

## Marketing Analyses

- `campaign_roi_comparison.sql`: Compares the ROI of different marketing campaigns
- `marketing_channel_effectiveness.sql`: Analyzes the effectiveness of marketing channels
- `customer_acquisition_by_campaign.sql`: Examines customer acquisition by campaign

## Inventory Analyses

- `stock_out_risk_analysis.sql`: Identifies products at risk of stocking out
- `inventory_turnover_analysis.sql`: Analyzes inventory turnover by product and category
- `warehouse_efficiency_analysis.sql`: Examines warehouse efficiency metrics