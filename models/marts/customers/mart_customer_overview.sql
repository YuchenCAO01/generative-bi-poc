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