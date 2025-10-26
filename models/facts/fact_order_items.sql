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