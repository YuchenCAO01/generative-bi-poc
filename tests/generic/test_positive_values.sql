{% test positive_values(model, column_name) %}

with validation as (
    select
        {{ column_name }} as positive_field
    from {{ model }}
    where {{ column_name }} <= 0
)

select *
from validation

{% endtest %}