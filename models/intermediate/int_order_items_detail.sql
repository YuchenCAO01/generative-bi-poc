with stg_orders as (
    select * from {{ ref('orders') }}
),

stg_order_items as (
    select * from {{ ref('order_items') }}
),

stg_products as (
    select * from {{ ref('products') }}
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
        o.status as order_status,
        
        -- Product information
        p.name as product_name,
        p.category_id,
        
        -- Order item details
        oi.quantity,
        oi.unit_price,
        (oi.quantity * oi.unit_price) as item_total,
        
        -- Derived fields
        case
            when o.status = 'cancelled' then true
            else false
        end as is_item_cancelled,
        
        -- Metadata
        current_timestamp() as _transformed_at
    from stg_order_items oi
    inner join stg_orders o on oi.order_id = o.order_id
    inner join stg_products p on oi.product_id = p.product_id
)

select * from order_items_detail