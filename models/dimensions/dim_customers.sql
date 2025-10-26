with int_customer_orders as (
    select * from {{ ref('int_customer_orders') }}
),

stg_customers as (
    select * from {{ ref('customers') }}
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
        concat(c.first_name, ' ', c.last_name) as full_name,
        
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