with stg_website_events as (
    select * from {{ ref('website_events') }}
),

-- Aggregate website events by customer and session
fact_website_events as (
    select
        -- Primary key (composite)
        event_id,
        
        -- Foreign keys
        session_id,
        customer_id,
        product_id,
        
        -- Event attributes
        event_type,
        page_url,
        split(page_url, '/')[safe_offset(3)] as page_path,
        device_type,
        
        -- Event flags
        case when event_type = 'purchase' then true else false end as is_purchase_event,
        case when event_type = 'add_to_cart' then true else false end as is_add_to_cart_event,
        
        -- Timestamps
        created_at as event_timestamp,
        
        -- Add metadata fields
        '{{ invocation_id }}' as _invocation_id,
        current_timestamp() as _loaded_at
    from stg_website_events
)

select * from fact_website_events