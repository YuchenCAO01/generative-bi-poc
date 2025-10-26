{% macro safe_divide(numerator, denominator) %}

{# This macro safely handles division by zero #}
{# Returns null when denominator is zero or null #}

case
    when {{ denominator }} is null then null
    when {{ denominator }} = 0 then null
    else {{ numerator }} / {{ denominator }}
end

{% endmacro %}