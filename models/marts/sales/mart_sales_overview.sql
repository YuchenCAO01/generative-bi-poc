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

-- Create sales overview mart
sales_overview_mart as (
    select
        -- Date attributes
        o.order_date_id as date_id,
        o.order_date_id as calendar_date,
        extract(year from o.order_date_id) as year,
        extract(quarter from o.order_date_id) as quarter,
        extract(month from o.order_date_id) as month,
        format_date('%B', o.order_date_id) as month_name,
        extract(day from o.order_date_id) as day_of_month,
        
        -- Order metrics
        count(distinct o.order_id) as order_count,
        sum(o.total_amount) as total_revenue,
        avg(o.total_amount) as average_order_value,
        
        -- Order item metrics
        sum(oi.quantity) as total_units_sold,
        count(distinct oi.product_id) as unique_products_sold,
        
        -- Customer metrics
        count(distinct o.customer_id) as customer_count,
        
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
    group by 1, 2, 3, 4, 5, 6, 7
)

select * from sales_overview_mart