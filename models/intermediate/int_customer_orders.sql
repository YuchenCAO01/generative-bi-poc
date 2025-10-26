with stg_customers as (
    select * from {{ ref('customers') }}
),

stg_orders as (
    select * from {{ ref('orders') }}
),

-- Aggregate order information by customer
customer_orders as (
    select
        -- Customer information
        c.customer_id,
        c.email,
        concat(c.first_name, ' ', c.last_name) as full_name,
        
        -- Order counts
        count(distinct o.order_id) as order_count,
        sum(case when o.status = 'cancelled' then 1 else 0 end) as cancelled_order_count,
        
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