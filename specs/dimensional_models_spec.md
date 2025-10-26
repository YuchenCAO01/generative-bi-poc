# Dimensional Models Specification

Dimensional models follow the Kimball methodology to create a star schema with dimension and fact tables. These models build upon the intermediate models and provide a structured approach for analytics. For an e-commerce analytics project on BigQuery, these models would be placed in the `models/dimensions/` and `models/facts/` directories.

## Dimension Models

Dimension tables contain descriptive attributes about business entities such as customers, products, and dates. They provide context for the metrics in fact tables.

### Example Dimension Models

#### 1. dim_customers.sql

```sql
with int_customer_orders as (
    select * from {{ ref('int_customer_orders') }}
),

stg_customers as (
    select * from {{ ref('stg_customers') }}
),

-- Create customer dimension with order metrics
customer_dimension as (
    select
        -- Primary key
        c.customer_id,
        
        -- Customer attributes
        c.email,
        c.first_name,
        c.last_name,
        c.full_name,
        
        -- Customer segmentation
        case
            when co.order_count > 10 then 'High'
            when co.order_count > 5 then 'Medium'
            when co.order_count > 0 then 'Low'
            else 'None'
        end as frequency_segment,
        
        case
            when co.lifetime_value > 1000 then 'High'
            when co.lifetime_value > 500 then 'Medium'
            when co.lifetime_value > 0 then 'Low'
            else 'None'
        end as value_segment,
        
        -- Order metrics
        co.order_count,
        co.cancelled_order_count,
        co.lifetime_value,
        co.average_order_value,
        
        -- First and last order dates
        co.first_order_date,
        co.most_recent_order_date,
        co.customer_tenure_days,
        
        -- Derived fields
        case
            when date_diff(current_date(), co.most_recent_order_date, day) <= 90 then true
            else false
        end as is_active_90d,
        
        -- Timestamps
        c.created_at,
        c.updated_at,
        
        -- Metadata
        current_timestamp() as _loaded_at
    from stg_customers c
    left join int_customer_orders co on c.customer_id = co.customer_id
)

select * from customer_dimension
```

#### 2. dim_products.sql

```sql
with int_product_order_metrics as (
    select * from {{ ref('int_product_order_metrics') }}
),

stg_products as (
    select * from {{ ref('stg_products') }}
),

stg_product_categories as (
    select * from {{ ref('stg_product_categories') }}
),

-- Create product dimension with category information and metrics
product_dimension as (
    select
        -- Primary key
        p.product_id,
        
        -- Product attributes
        p.product_name,
        p.product_description,
        p.price,
        
        -- Category information
        p.category_id,
        pc.name as category_name,
        
        -- Product performance metrics
        pom.order_count,
        pom.customer_count,
        pom.total_quantity_sold,
        pom.total_revenue,
        pom.return_rate,
        
        -- Product segmentation
        case
            when pom.total_revenue > 10000 then 'High'
            when pom.total_revenue > 1000 then 'Medium'
            else 'Low'
        end as revenue_segment,
        
        case
            when pom.return_rate > 0.1 then 'High'
            when pom.return_rate > 0.05 then 'Medium'
            else 'Low'
        end as return_rate_segment,
        
        -- Timestamps
        p.created_at,
        p.updated_at,
        
        -- Metadata
        current_timestamp() as _loaded_at
    from stg_products p
    left join stg_product_categories pc on p.category_id = pc.category_id
    left join int_product_order_metrics pom on p.product_id = pom.product_id
)

select * from product_dimension
```

#### 3. dim_dates.sql

```sql
-- Generate a date dimension table
with date_spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2020-01-01' as date)",
        end_date="cast(date_add(current_date(), interval 1 year) as date)"
    ) }}
),

-- Create date dimension with various date attributes
date_dimension as (
    select
        -- Primary key
        date_day as date_id,
        
        -- Date attributes
        date_day as calendar_date,
        extract(year from date_day) as year,
        extract(quarter from date_day) as quarter,
        extract(month from date_day) as month,
        extract(day from date_day) as day_of_month,
        extract(dayofweek from date_day) as day_of_week,
        extract(dayofyear from date_day) as day_of_year,
        
        -- Month names
        format_date('%B', date_day) as month_name,
        format_date('%b', date_day) as month_name_short,
        
        -- Day names
        format_date('%A', date_day) as day_name,
        format_date('%a', date_day) as day_name_short,
        
        -- Week attributes
        extract(week from date_day) as week_of_year,
        
        -- Fiscal periods (assuming fiscal year starts in February)
        case
            when extract(month from date_day) = 1 then extract(year from date_day) - 1
            else extract(year from date_day)
        end as fiscal_year,
        
        -- Holiday flags (example for US holidays)
        case
            when format_date('%m-%d', date_day) = '01-01' then 'New Year''s Day'
            when format_date('%m-%d', date_day) = '07-04' then 'Independence Day'
            when format_date('%m-%d', date_day) = '12-25' then 'Christmas Day'
            else null
        end as holiday_name,
        
        case
            when format_date('%m-%d', date_day) in ('01-01', '07-04', '12-25') then true
            else false
        end as is_holiday,
        
        -- Weekend flag
        case
            when extract(dayofweek from date_day) in (1, 7) then true
            else false
        end as is_weekend,
        
        -- Metadata
        current_timestamp() as _loaded_at
    from date_spine
)

select * from date_dimension
```

## Fact Models

Fact tables contain the measurable, quantitative data about business processes. They connect to dimension tables via foreign keys.

### Example Fact Models

#### 1. fact_orders.sql

```sql
with stg_orders as (
    select * from {{ ref('stg_orders') }}
),

int_customer_orders as (
    select * from {{ ref('int_customer_orders') }}
),

-- Create order fact table
order_fact as (
    select
        -- Primary key
        o.order_id,
        
        -- Foreign keys to dimensions
        o.customer_id,
        cast(o.order_date as date) as order_date_id,
        
        -- Order attributes
        o.order_status,
        o.total_amount,
        
        -- Order flags
        o.is_cancelled,
        o.is_delivered,
        
        -- Customer context at time of order
        co.order_count as customer_previous_order_count,
        
        -- Timestamps
        o.created_at,
        o.updated_at,
        
        -- Metadata
        current_timestamp() as _loaded_at
    from stg_orders o
    left join int_customer_orders co on o.customer_id = co.customer_id
)

select * from order_fact
```

#### 2. fact_order_items.sql

```sql
with int_order_items_detail as (
    select * from {{ ref('int_order_items_detail') }}
),

-- Create order items fact table
order_items_fact as (
    select
        -- Primary key
        oi.order_item_id,
        
        -- Foreign keys to dimensions
        oi.order_id,
        oi.product_id,
        oi.customer_id,
        cast(oi.order_date as date) as order_date_id,
        
        -- Order item attributes
        oi.quantity,
        oi.unit_price,
        oi.item_total,
        
        -- Order context
        oi.order_status,
        oi.is_item_cancelled,
        
        -- Metadata
        current_timestamp() as _loaded_at
    from int_order_items_detail oi
)

select * from order_items_fact
```

#### 3. fact_website_events.sql

```sql
with stg_website_events as (
    select * from {{ ref('stg_website_events') }}
),

-- Create website events fact table
website_events_fact as (
    select
        -- Primary key
        e.event_id,
        
        -- Foreign keys to dimensions
        e.customer_id,
        e.product_id,
        cast(e.created_at as date) as event_date_id,
        
        -- Event attributes
        e.session_id,
        e.event_type,
        e.page_url,
        e.page_path,
        e.device_type,
        
        -- Event flags
        e.is_purchase_event,
        e.is_add_to_cart_event,
        
        -- Timestamps
        e.created_at,
        
        -- Metadata
        current_timestamp() as _loaded_at
    from stg_website_events e
)

select * from website_events_fact
```

#### 4. fact_inventory_snapshots.sql

```sql
with stg_inventory as (
    select * from {{ ref('stg_inventory') }}
),

-- Create inventory snapshot fact table
inventory_snapshot_fact as (
    select
        -- Primary key (composite)
        concat(i.product_id, '-', i.warehouse_id, '-', cast(i.updated_at as string)) as inventory_snapshot_id,
        
        -- Foreign keys to dimensions
        i.product_id,
        i.warehouse_id,
        cast(i.updated_at as date) as snapshot_date_id,
        
        -- Inventory attributes
        i.quantity_on_hand,
        
        -- Derived fields
        case
            when i.quantity_on_hand = 0 then true
            else false
        end as is_out_of_stock,
        
        -- Timestamps
        i.created_at,
        i.updated_at,
        
        -- Metadata
        current_timestamp() as _loaded_at
    from stg_inventory i
)

select * from inventory_snapshot_fact
```

## Dimensional Modeling Best Practices

1. **Follow Star Schema Design**:
   - Clear separation between dimensions and facts
   - Denormalized dimension tables
   - Normalized fact tables with foreign keys to dimensions

2. **Dimension Table Design**:
   - Include descriptive attributes
   - Use surrogate keys when appropriate
   - Include effective dates for slowly changing dimensions
   - Denormalize hierarchies into a single dimension

3. **Fact Table Design**:
   - Include foreign keys to all related dimensions
   - Include measurable metrics
   - Minimize text fields in fact tables
   - Consider grain carefully (level of detail)

4. **Performance Optimization**:
   - Partition fact tables by date
   - Cluster large tables by frequently filtered columns
   - Consider materialization strategy (table vs. view)

5. **Documentation**:
   - Document the grain of each fact table
   - Explain relationships between facts and dimensions
   - Document business definitions of metrics

## Schema.yml for Dimensional Models

Create schema.yml files in both the dimensions and facts directories:

### models/dimensions/schema.yml

```yaml
version: 2

models:
  - name: dim_customers
    description: "Customer dimension with attributes and metrics"
    columns:
      - name: customer_id
        description: "The primary key for the customer dimension"
        tests:
          - unique
          - not_null
      # Additional columns...

  - name: dim_products
    description: "Product dimension with attributes and metrics"
    columns:
      - name: product_id
        description: "The primary key for the product dimension"
        tests:
          - unique
          - not_null
      # Additional columns...

  - name: dim_dates
    description: "Date dimension with calendar attributes"
    columns:
      - name: date_id
        description: "The primary key for the date dimension"
        tests:
          - unique
          - not_null
      # Additional columns...
```

### models/facts/schema.yml

```yaml
version: 2

models:
  - name: fact_orders
    description: "Order fact table at the order header level"
    columns:
      - name: order_id
        description: "The primary key for the order fact table"
        tests:
          - unique
          - not_null
      - name: customer_id
        description: "Foreign key to the customer dimension"
        tests:
          - not_null
          - relationships:
              to: ref('dim_customers')
              field: customer_id
      # Additional columns...

  - name: fact_order_items
    description: "Order items fact table at the line item level"
    columns:
      - name: order_item_id
        description: "The primary key for the order items fact table"
        tests:
          - unique
          - not_null
      # Additional columns...

  # Additional models...
```

## Dimensional Models Directory Structure

```
models/
├── dimensions/
│   ├── schema.yml
│   ├── dim_customers.sql
│   ├── dim_products.sql
│   └── dim_dates.sql
└── facts/
    ├── schema.yml
    ├── fact_orders.sql
    ├── fact_order_items.sql
    ├── fact_website_events.sql
    └── fact_inventory_snapshots.sql