{% macro categorize_customer(order_count, lifetime_value) %}

{# This macro categorizes customers based on order count and lifetime value #}
{# Returns a customer segment label #}

case
    when {{ order_count }} > 10 and {{ lifetime_value }} > 1000 then 'High Value'
    when {{ order_count }} > 5 and {{ lifetime_value }} > 500 then 'Medium Value'
    when {{ order_count }} > 0 then 'Low Value'
    else 'New'
end

{% endmacro %}