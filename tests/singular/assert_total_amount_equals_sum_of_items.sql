-- Test that order total_amount equals the sum of order_items
with order_totals as (
    select
        order_id,
        total_amount as order_total
    from {{ ref('fact_orders') }}
),

item_totals as (
    select
        order_id,
        sum(item_total) as sum_of_items
    from {{ ref('fact_order_items') }}
    group by 1
),

validation as (
    select
        o.order_id,
        o.order_total,
        i.sum_of_items,
        abs(o.order_total - i.sum_of_items) as difference
    from order_totals o
    inner join item_totals i on o.order_id = i.order_id
    where abs(o.order_total - i.sum_of_items) > 0.01  -- Allow for small rounding differences
)

select *
from validation