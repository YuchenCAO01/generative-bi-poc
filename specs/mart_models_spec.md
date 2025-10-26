# Mart Models Specification

Mart models are the final layer in the dbt project, designed specifically for reporting and analytics use cases. They combine facts and dimensions into business-specific models that are optimized for specific analytical domains. For an e-commerce analytics project on BigQuery, these models would be placed in the `models/marts/` directory, organized by business domain.

## Mart Model Structure

Each mart model should follow this general pattern:

```sql
with fact_table as (
    select * from {{ ref('fact_table') }}
),

dimension_1 as (
    select * from {{ ref('dim_table_1') }}
),

dimension_2 as (
    select * from {{ ref('dim_table_2') }}
),

-- Join facts and dimensions for specific business domain
mart_model as (
    select
        -- Primary keys from fact table
        f.fact_id,
        
        -- Foreign keys to dimensions
        f.dimension_1_id,
        f.dimension_2_id,
        
        -- Dimension attributes
        d1.attribute_1 as dimension_1_attribute_1,
        d1.attribute_2 as dimension_1_attribute_2,
        d2.attribute_1 as dimension_2_attribute_1,
        
        -- Metrics from fact table
        f.metric_1,
        f.metric_2,
        
        -- Calculated metrics
        f.metric_1 / f.metric_2 as calculated_metric,
        
        -- Metadata
        current_timestamp() as _loaded_at
    from fact_table f
    left join dimension_1 d1 on f.dimension_1_id = d1.dimension_1_id
    left join dimension_2 d2 on f.dimension_2_id = d2.dimension_2_id
)

select * from mart_model
```

## Example Mart Models

### Marketing Marts

#### 1. marketing/mart_campaign_performance.sql

```sql
with fact_orders as (
    select * from {{ ref('fact_orders') }}
),

dim_customers as (
    select * from {{ ref('dim_customers') }}
),

dim_dates as (
    select * from {{ ref('dim_dates') }}
),

stg_marketing_campaigns as (
    select * from {{ ref('stg_marketing_campaigns') }}
),

-- Create marketing campaign performance mart
campaign_performance_mart as (
    select
        -- Campaign information
        c.campaign_id,
        c.name as campaign_name,
        c.type as campaign_type,
        c.start_date,
        c.end_date,
        
        -- Date attributes
        d.year,
        d.quarter,
        d.month,
        d.month_name,
        
        -- Customer segments
        c.value_segment as customer_value_segment,
        c.frequency_segment as customer_frequency_segment,
        
        -- Order metrics
        count(distinct o.order_id) as order_count,
        sum(o.total_amount) as total_revenue,
        avg(o.total_amount) as average_order_value,
        
        -- Customer metrics
        count(distinct o.customer_id) as customer_count,
        
        -- Campaign metrics
        c.budget as campaign_budget,
        sum(o.total_amount) - c.budget as campaign_profit,
        safe_divide(
            sum(o.total_amount) - c.budget,
            c.budget
        ) as campaign_roi,
        
        -- Cost metrics
        safe_divide(
            c.budget,
            count(distinct o.order_id)
        ) as cost_per_order,
        
        safe_divide(
            c.budget,
            count(distinct o.customer_id)
        ) as cost_per_customer,
        
        -- Metadata
        current_timestamp() as _loaded_at
    from stg_marketing_campaigns c
    left join fact_orders o on 
        o.order_date between c.start_date and c.end_date
        and o.campaign_id = c.campaign_id
    left join dim_customers cust on o.customer_id = cust.customer_id
    left join dim_dates d on o.order_date_id = d.date_id
    group by 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 22
)

select * from campaign_performance_mart
```

### Sales Marts

#### 2. sales/mart_sales_overview.sql

```sql
with fact_orders as (
    select * from {{ ref('fact_orders') }}
),

fact_order_items as (
    select * from {{ ref('fact_order_items') }}
),

dim_customers as (
    select * from {{ ref('dim_customers') }}
),

dim_products as (
    select * from {{ ref('dim_products') }}
),

dim_dates as (
    select * from {{ ref('dim_dates') }}
),

-- Create sales overview mart
sales_overview_mart as (
    select
        -- Date attributes
        d.date_id,
        d.calendar_date,
        d.year,
        d.quarter,
        d.month,
        d.month_name,
        d.day_of_month,
        
        -- Order metrics
        count(distinct o.order_id) as order_count,
        sum(o.total_amount) as total_revenue,
        avg(o.total_amount) as average_order_value,
        
        -- Order item metrics
        sum(oi.quantity) as total_units_sold,
        count(distinct oi.product_id) as unique_products_sold,
        
        -- Customer metrics
        count(distinct o.customer_id) as customer_count,
        
        -- Product metrics
        sum(case when p.category_name = 'Electronics' then oi.item_total else 0 end) as electronics_revenue,
        sum(case when p.category_name = 'Clothing' then oi.item_total else 0 end) as clothing_revenue,
        sum(case when p.category_name = 'Home' then oi.item_total else 0 end) as home_revenue,
        
        -- Status metrics
        sum(case when o.order_status = 'completed' then o.total_amount else 0 end) as completed_revenue,
        sum(case when o.order_status = 'cancelled' then o.total_amount else 0 end) as cancelled_revenue,
        
        -- Calculated metrics
        safe_divide(
            sum(case when o.order_status = 'cancelled' then o.total_amount else 0 end),
            sum(o.total_amount)
        ) as cancellation_rate,
        
        -- Metadata
        current_timestamp() as _loaded_at
    from fact_orders o
    left join fact_order_items oi on o.order_id = oi.order_id
    left join dim_customers c on o.customer_id = c.customer_id
    left join dim_products p on oi.product_id = p.product_id
    left join dim_dates d on o.order_date_id = d.date_id
    group by 1, 2, 3, 4, 5, 6, 7
)

select * from sales_overview_mart
```

#### 3. sales/mart_product_performance.sql

```sql
with fact_order_items as (
    select * from {{ ref('fact_order_items') }}
),

dim_products as (
    select * from {{ ref('dim_products') }}
),

dim_dates as (
    select * from {{ ref('dim_dates') }}
),

-- Create product performance mart
product_performance_mart as (
    select
        -- Product attributes
        p.product_id,
        p.product_name,
        p.category_id,
        p.category_name,
        p.price,
        
        -- Date attributes
        d.year,
        d.quarter,
        d.month,
        d.month_name,
        
        -- Sales metrics
        count(distinct oi.order_id) as order_count,
        sum(oi.quantity) as units_sold,
        sum(oi.item_total) as total_revenue,
        
        -- Product performance
        p.total_quantity_sold as lifetime_units_sold,
        p.total_revenue as lifetime_revenue,
        p.return_rate,
        
        -- Product segmentation
        p.revenue_segment,
        p.return_rate_segment,
        
        -- Calculated metrics
        safe_divide(
            sum(oi.item_total),
            sum(oi.quantity)
        ) as average_selling_price,
        
        -- Metadata
        current_timestamp() as _loaded_at
    from fact_order_items oi
    inner join dim_products p on oi.product_id = p.product_id
    inner join dim_dates d on oi.order_date_id = d.date_id
    group by 1, 2, 3, 4, 5, 6, 7, 8, 9, 14, 15, 16, 17, 18
)

select * from product_performance_mart
```

### Customer Marts

#### 4. customers/mart_customer_overview.sql

```sql
with dim_customers as (
    select * from {{ ref('dim_customers') }}
),

fact_orders as (
    select * from {{ ref('fact_orders') }}
),

fact_website_events as (
    select * from {{ ref('fact_website_events') }}
),

-- Create customer overview mart
customer_overview_mart as (
    select
        -- Customer attributes
        c.customer_id,
        c.email,
        c.full_name,
        c.created_at as customer_created_at,
        
        -- Customer segments
        c.frequency_segment,
        c.value_segment,
        
        -- Order metrics
        c.order_count,
        c.cancelled_order_count,
        c.lifetime_value,
        c.average_order_value,
        
        -- Order dates
        c.first_order_date,
        c.most_recent_order_date,
        c.customer_tenure_days,
        
        -- Activity flags
        c.is_active_90d,
        
        -- Website activity
        count(distinct e.session_id) as website_session_count,
        sum(case when e.event_type = 'page_view' then 1 else 0 end) as page_view_count,
        sum(case when e.event_type = 'product_view' then 1 else 0 end) as product_view_count,
        sum(case when e.event_type = 'add_to_cart' then 1 else 0 end) as add_to_cart_count,
        
        -- Conversion metrics
        safe_divide(
            c.order_count,
            sum(case when e.event_type = 'add_to_cart' then 1 else 0 end)
        ) as cart_to_purchase_rate,
        
        -- Metadata
        current_timestamp() as _loaded_at
    from dim_customers c
    left join fact_website_events e on c.customer_id = e.customer_id
    group by 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14
)

select * from customer_overview_mart
```

#### 5. customers/mart_customer_cohorts.sql

```sql
with dim_customers as (
    select * from {{ ref('dim_customers') }}
),

fact_orders as (
    select * from {{ ref('fact_orders') }}
),

dim_dates as (
    select * from {{ ref('dim_dates') }}
),

-- Create customer cohorts by acquisition month
customer_cohorts as (
    select
        -- Cohort definition (acquisition month)
        date_trunc(c.first_order_date, month) as cohort_month,
        
        -- Date attributes for analysis period
        d.year,
        d.quarter,
        d.month,
        
        -- Calculate months since first order
        date_diff(
            date_trunc(o.order_date, month),
            date_trunc(c.first_order_date, month),
            month
        ) as months_since_first_order,
        
        -- Cohort metrics
        count(distinct c.customer_id) as cohort_size,
        count(distinct o.order_id) as order_count,
        sum(o.total_amount) as total_revenue,
        
        -- Retention metrics
        count(distinct o.customer_id) as active_customers,
        safe_divide(
            count(distinct o.customer_id),
            count(distinct c.customer_id)
        ) as retention_rate,
        
        -- Revenue metrics
        safe_divide(
            sum(o.total_amount),
            count(distinct o.customer_id)
        ) as average_revenue_per_active_customer,
        
        -- Metadata
        current_timestamp() as _loaded_at
    from dim_customers c
    left join fact_orders o on c.customer_id = o.customer_id
    left join dim_dates d on o.order_date_id = d.date_id
    where c.first_order_date is not null
    group by 1, 2, 3, 4, 5
)

select * from customer_cohorts
```

## Mart Models Best Practices

1. **Business Domain Organization**:
   - Organize marts by business domain (marketing, sales, customers)
   - Create marts that answer specific business questions
   - Design for specific reporting and dashboard needs

2. **Denormalized Design**:
   - Include all relevant dimension attributes
   - Pre-calculate common metrics
   - Optimize for query performance

3. **Consistent Naming**:
   - Use consistent naming across all marts
   - Clearly indicate the business domain in the model name
   - Use descriptive column names

4. **Documentation**:
   - Document the business purpose of each mart
   - Explain key metrics and calculations
   - Include example use cases

5. **Performance Optimization**:
   - Materialize as tables for query performance
   - Partition by date for large datasets
   - Cluster by commonly filtered dimensions

6. **Testing**:
   - Test key metrics and calculations
   - Validate against source data
   - Ensure consistency across marts

## Schema.yml for Mart Models

Create schema.yml files in each mart subdirectory:

### models/marts/marketing/schema.yml

```yaml
version: 2

models:
  - name: mart_campaign_performance
    description: "Marketing campaign performance metrics for analysis and reporting"
    columns:
      - name: campaign_id
        description: "The primary key for marketing campaigns"
        tests:
          - not_null
      # Additional columns...
```

### models/marts/sales/schema.yml

```yaml
version: 2

models:
  - name: mart_sales_overview
    description: "Sales overview metrics aggregated by date"
    columns:
      - name: date_id
        description: "The primary key (date) for this mart"
        tests:
          - not_null
      # Additional columns...

  - name: mart_product_performance
    description: "Product performance metrics for sales analysis"
    columns:
      - name: product_id
        description: "The primary key for products"
        tests:
          - not_null
      # Additional columns...
```

### models/marts/customers/schema.yml

```yaml
version: 2

models:
  - name: mart_customer_overview
    description: "Customer overview with order history and website activity"
    columns:
      - name: customer_id
        description: "The primary key for customers"
        tests:
          - unique
          - not_null
      # Additional columns...

  - name: mart_customer_cohorts
    description: "Customer cohort analysis by acquisition month"
    columns:
      - name: cohort_month
        description: "The cohort month (acquisition month)"
        tests:
          - not_null
      # Additional columns...
```

## Mart Models Directory Structure

```
models/
└── marts/
    ├── marketing/
    │   ├── schema.yml
    │   └── mart_campaign_performance.sql
    ├── sales/
    │   ├── schema.yml
    │   ├── mart_sales_overview.sql
    │   └── mart_product_performance.sql
    └── customers/
        ├── schema.yml
        ├── mart_customer_overview.sql
        └── mart_customer_cohorts.sql