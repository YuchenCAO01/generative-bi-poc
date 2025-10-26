/*
  Analysis: Customer Cohort Retention
  
  This analysis examines customer retention by cohort (acquisition month).
  It shows what percentage of customers from each cohort continue to place
  orders in subsequent months.
*/

with dim_customers as (
    select * from {{ ref('dim_customers') }}
),

fact_orders as (
    select * from {{ ref('fact_orders') }}
),

-- Create cohorts based on first order month
customer_cohorts as (
    select
        customer_id,
        date_trunc(first_order_date, month) as cohort_month
    from dim_customers
    where first_order_date is not null
),

-- Get all orders with cohort information
cohort_orders as (
    select
        c.customer_id,
        c.cohort_month,
        date_trunc(o.order_date_id, month) as order_month,
        date_diff(
            date_trunc(o.order_date_id, month),
            c.cohort_month,
            month
        ) as months_since_first_order
    from customer_cohorts c
    inner join fact_orders o on c.customer_id = o.customer_id
),

-- Count distinct customers by cohort and month
cohort_retention as (
    select
        cohort_month,
        months_since_first_order,
        count(distinct customer_id) as customer_count
    from cohort_orders
    group by 1, 2
),

-- Calculate cohort sizes
cohort_sizes as (
    select
        cohort_month,
        count(distinct customer_id) as cohort_size
    from customer_cohorts
    group by 1
),

-- Calculate retention rates
retention_rates as (
    select
        cr.cohort_month,
        cr.months_since_first_order,
        cr.customer_count,
        cs.cohort_size,
        round(safe_divide(cr.customer_count, cs.cohort_size) * 100, 2) as retention_rate
    from cohort_retention cr
    inner join cohort_sizes cs on cr.cohort_month = cs.cohort_month
    order by 1, 2
)

select * from retention_rates