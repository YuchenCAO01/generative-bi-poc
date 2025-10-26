# Intermediate Models Specification

Intermediate models build upon staging models to implement business logic and prepare data for dimensional modeling. They serve as a bridge between raw data and final analytical models. For an e-commerce analytics project on BigQuery, these models would be placed in the `models/intermediate/` directory.

## Intermediate Model Structure

Each intermediate model should follow this general pattern:

```sql
with stg_table_1 as (
    select * from {{ ref('stg_table_1') }}
),

stg_table_2 as (
    select * from {{ ref('stg_table_2') }}
),

-- Implement business logic
transformed as (
    select
        -- Primary keys
        t1.table_1_id,
        
        -- Join to related tables
        t2.table_2_id,
        
        -- Business logic transformations
        case
            when t1.status = 'completed' and t2.is_valid then 'valid'
            when t1.status = 'completed' and not t2.is_valid then 'invalid'
            else 'pending'
        end as validation_status,
        
        -- Calculations
        t1.amount * t2.rate as calculated_amount,
        
        -- Date/time transformations
        date_diff(t1.end_date, t1.start_date, day) as duration_days,
        
        -- Window functions
        sum(t1.amount) over (partition by t1.customer_id) as customer_total,
        
        -- Metadata
        current_timestamp() as _transformed_at
    from stg_table_1 t1
    left join stg_table_2 t2 on t1.table_2_id = t2.table_2_id
)

select * from transformed
```

## Example Intermediate Models

### 1. int_customer_orders.sql

```sql
with stg_customers as (
    select * from {{ ref('stg_customers') }}
),

stg_orders as (
    select * from {{ ref('stg_orders') }}
),

-- Aggregate order information by customer
customer_orders as (
    select
        -- Customer information
        c.customer_id,
        c.email,
        c.full_name,
        
        -- Order counts
        count(distinct o.order_id) as order_count,
        sum(case when o.is_cancelled then 1 else 0 end) as cancelled_order_count,
        
        -- Order values
        sum(o.total_amount) as lifetime_value,
        avg(o.total_amount) as average_order_value,
        
        -- First and last order dates
        min(o.order_date) as first_order_date,
        max(o.order_date) as most_recent_order_date,
        
        -- Days between first and last order
        date_diff(max(o.order_date), min(o.order_date), day) as customer_tenure_days,
        
        -- Metadata
        current_timestamp() as _transformed_at
    from stg_customers c
    left join stg_orders o on c.customer_id = o.customer_id
    group by 1, 2, 3
)

select * from customer_orders
```

### 2. int_order_items_detail.sql

```sql
with stg_orders as (
    select * from {{ ref('stg_orders') }}
),

stg_order_items as (
    select * from {{ ref('stg_order_items') }}
),

stg_products as (
    select * from {{ ref('stg_products') }}
),

-- Join order items with orders and products
order_items_detail as (
    select
        -- Order item keys
        oi.order_item_id,
        oi.order_id,
        oi.product_id,
        
        -- Order information
        o.order_date,
        o.customer_id,
        o.order_status,
        
        -- Product information
        p.product_name,
        p.category_id,
        
        -- Order item details
        oi.quantity,
        oi.unit_price,
        oi.item_total,
        
        -- Derived fields
        case
            when o.is_cancelled then true
            else false
        end as is_item_cancelled,
        
        -- Metadata
        current_timestamp() as _transformed_at
    from stg_order_items oi
    inner join stg_orders o on oi.order_id = o.order_id
    inner join stg_products p on oi.product_id = p.product_id
)

select * from order_items_detail
```

### 3. int_product_order_metrics.sql

```sql
with stg_products as (
    select * from {{ ref('stg_products') }}
),

stg_order_items as (
    select * from {{ ref('stg_order_items') }}
),

stg_orders as (
    select * from {{ ref('stg_orders') }}
),

-- Calculate product metrics from order data
product_metrics as (
    select
        -- Product information
        p.product_id,
        p.product_name,
        p.category_id,
        
        -- Order counts
        count(distinct oi.order_id) as order_count,
        count(distinct o.customer_id) as customer_count,
        
        -- Quantity metrics
        sum(oi.quantity) as total_quantity_sold,
        
        -- Revenue metrics
        sum(oi.item_total) as total_revenue,
        
        -- Calculate product return rate
        sum(case when o.order_status = 'returned' then oi.quantity else 0 end) as quantity_returned,
        safe_divide(
            sum(case when o.order_status = 'returned' then oi.quantity else 0 end),
            sum(oi.quantity)
        ) as return_rate,
        
        -- Metadata
        current_timestamp() as _transformed_at
    from stg_products p
    left join stg_order_items oi on p.product_id = oi.product_id
    left join stg_orders o on oi.order_id = o.order_id
    group by 1, 2, 3
)

select * from product_metrics
```

### 4. int_customer_website_activity.sql

```sql
with stg_customers as (
    select * from {{ ref('stg_customers') }}
),

stg_website_events as (
    select * from {{ ref('stg_website_events') }}
),

-- Aggregate website activity by customer
customer_activity as (
    select
        -- Customer information
        c.customer_id,
        c.email,
        
        -- Session counts
        count(distinct e.session_id) as session_count,
        
        -- Event counts by type
        sum(case when e.event_type = 'page_view' then 1 else 0 end) as page_view_count,
        sum(case when e.event_type = 'product_view' then 1 else 0 end) as product_view_count,
        sum(case when e.event_type = 'add_to_cart' then 1 else 0 end) as add_to_cart_count,
        sum(case when e.event_type = 'checkout' then 1 else 0 end) as checkout_count,
        sum(case when e.event_type = 'purchase' then 1 else 0 end) as purchase_count,
        
        -- Conversion metrics
        safe_divide(
            sum(case when e.event_type = 'purchase' then 1 else 0 end),
            sum(case when e.event_type = 'product_view' then 1 else 0 end)
        ) as product_to_purchase_rate,
        
        safe_divide(
            sum(case when e.event_type = 'purchase' then 1 else 0 end),
            sum(case when e.event_type = 'add_to_cart' then 1 else 0 end)
        ) as cart_to_purchase_rate,
        
        -- Device metrics
        sum(case when e.device_type = 'desktop' then 1 else 0 end) as desktop_event_count,
        sum(case when e.device_type = 'mobile' then 1 else 0 end) as mobile_event_count,
        sum(case when e.device_type = 'tablet' then 1 else 0 end) as tablet_event_count,
        
        -- Metadata
        current_timestamp() as _transformed_at
    from stg_customers c
    inner join stg_website_events e on c.customer_id = e.customer_id
    group by 1, 2
)

select * from customer_activity
```

### 5. int_marketing_campaign_performance.sql

```sql
with stg_marketing_campaigns as (
    select * from {{ ref('stg_marketing_campaigns') }}
),

stg_orders as (
    select * from {{ ref('stg_orders') }}
),

-- Calculate campaign performance metrics
campaign_performance as (
    select
        -- Campaign information
        c.campaign_id,
        c.name as campaign_name,
        c.type as campaign_type,
        c.start_date,
        c.end_date,
        c.budget,
        
        -- Date metrics
        date_diff(c.end_date, c.start_date, day) as campaign_duration_days,
        
        -- Order metrics
        count(distinct o.order_id) as order_count,
        sum(o.total_amount) as total_revenue,
        
        -- ROI calculations
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
        
        -- Metadata
        current_timestamp() as _transformed_at
    from stg_marketing_campaigns c
    left join stg_orders o on 
        o.order_date between c.start_date and c.end_date
        and o.campaign_id = c.campaign_id
    group by 1, 2, 3, 4, 5, 6
)

select * from campaign_performance
```

## Intermediate Models Best Practices

1. **Focus on Business Logic**:
   - Implement complex business rules
   - Create reusable transformations
   - Prepare data for dimensional modeling

2. **Optimize Joins**:
   - Use appropriate join types (inner, left, etc.)
   - Join on the minimum required columns
   - Consider performance implications of joins

3. **Use Window Functions Effectively**:
   - Calculate running totals, ranks, etc.
   - Partition by appropriate dimensions
   - Consider performance implications

4. **Handle Null Values and Division by Zero**:
   - Use `safe_divide()` for division operations
   - Implement appropriate null handling
   - Use `coalesce()` for default values

5. **Document Business Logic**:
   - Explain complex calculations
   - Document business rules
   - Include references to requirements

6. **Testing**:
   - Test key business calculations
   - Validate aggregations
   - Ensure referential integrity

## Schema.yml for Intermediate Models

Create a `models/intermediate/schema.yml` file to document and test the intermediate models:

```yaml
version: 2

models:
  - name: int_customer_orders
    description: "Customer order metrics including lifetime value and order counts"
    columns:
      - name: customer_id
        description: "The primary key for customers"
        tests:
          - unique
          - not_null
      - name: lifetime_value
        description: "Total value of all customer orders"
        tests:
          - not_null
      # Additional columns...

  - name: int_order_items_detail
    description: "Detailed order item information with product and order data"
    columns:
      - name: order_item_id
        description: "The primary key for order items"
        tests:
          - unique
          - not_null
      # Additional columns...

  # Additional models...
```

## Intermediate Models Directory Structure

```
models/
└── intermediate/
    ├── schema.yml
    ├── int_customer_orders.sql
    ├── int_order_items_detail.sql
    ├── int_product_order_metrics.sql
    ├── int_customer_website_activity.sql
    └── int_marketing_campaign_performance.sql