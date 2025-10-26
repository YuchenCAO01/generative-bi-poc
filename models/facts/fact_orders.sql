with stg_orders as (
    select * from {{ ref('orders') }}
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
        o.status as order_status,
        o.total_amount,
        
        -- Order flags
        case when o.status = 'cancelled' then true else false end as is_cancelled,
        case when o.status = 'delivered' then true else false end as is_delivered,
        
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