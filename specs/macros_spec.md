# Macros Specification

Macros in dbt are reusable pieces of SQL code that can be called from models. They are similar to functions in other programming languages and help reduce code duplication, improve maintainability, and encapsulate complex logic. For an e-commerce analytics project on BigQuery, macros can be particularly useful for standardizing calculations, implementing business logic, and optimizing SQL patterns.

## Types of Macros

1. **Utility Macros**: General-purpose helpers for common operations
2. **Business Logic Macros**: Encapsulate specific business calculations
3. **Testing Macros**: Custom test logic for data validation
4. **BigQuery-Specific Macros**: Optimizations for BigQuery

## Example Macro Files

### 1. Utility Macros

#### macros/utils/date_spine.sql

```sql
{% macro date_spine(start_date, end_date, datepart) %}

{# This macro generates a date spine between start_date and end_date #}
{# Useful for creating date dimensions or filling in gaps in time series data #}

with date_spine as (
    {{ dbt_utils.date_spine(
        datepart=datepart,
        start_date=start_date,
        end_date=end_date
    ) }}
)

select * from date_spine

{% endmacro %}
```

#### macros/utils/safe_divide.sql

```sql
{% macro safe_divide(numerator, denominator) %}

{# This macro safely handles division by zero #}
{# Returns null when denominator is zero or null #}

case
    when {{ denominator }} is null then null
    when {{ denominator }} = 0 then null
    else {{ numerator }} / {{ denominator }}
end

{% endmacro %}
```

#### macros/utils/generate_surrogate_key.sql

```sql
{% macro generate_surrogate_key(field_list) %}

{# This macro generates a surrogate key from a list of fields #}
{# Uses MD5 hash for key generation #}

to_hex(md5(concat(
    {% for field in field_list %}
        coalesce(cast({{ field }} as string), '')
        {% if not loop.last %} || '|' || {% endif %}
    {% endfor %}
)))

{% endmacro %}
```

### 2. Business Logic Macros

#### macros/business_logic/calculate_customer_ltv.sql

```sql
{% macro calculate_customer_ltv(customer_id, order_amount, is_cancelled) %}

{# This macro calculates customer lifetime value #}
{# Includes only non-cancelled orders #}

sum(
    case
        when {{ is_cancelled }} = false then {{ order_amount }}
        else 0
    end
) over (
    partition by {{ customer_id }}
    order by {{ order_date }} rows between unbounded preceding and current row
)

{% endmacro %}
```

#### macros/business_logic/calculate_product_margin.sql

```sql
{% macro calculate_product_margin(selling_price, cost_price) %}

{# This macro calculates product margin percentage #}
{# Returns the margin as a decimal (e.g., 0.25 for 25%) #}

{{ safe_divide(
    selling_price - cost_price,
    selling_price
) }}

{% endmacro %}
```

#### macros/business_logic/categorize_customer.sql

```sql
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
```

### 3. BigQuery-Specific Macros

#### macros/bigquery/partition_by.sql

```sql
{% macro partition_by(field) %}

{# This macro generates BigQuery partition by clause #}
{# Optimizes query performance for large tables #}

partition by date({{ field }})

{% endmacro %}
```

#### macros/bigquery/cluster_by.sql

```sql
{% macro cluster_by(fields) %}

{# This macro generates BigQuery cluster by clause #}
{# Optimizes query performance for large tables #}

cluster by 
{% for field in fields %}
    {{ field }}{% if not loop.last %}, {% endif %}
{% endfor %}

{% endmacro %}
```

#### macros/bigquery/create_temp_table.sql

```sql
{% macro create_temp_table(table_name, sql) %}

{# This macro creates a temporary table in BigQuery #}
{# Useful for complex multi-step transformations #}

create or replace temporary table {{ table_name }} as (
    {{ sql }}
)

{% endmacro %}
```

### 4. Testing Macros

#### macros/testing/test_not_negative.sql

```sql
{% macro test_not_negative(model, column_name) %}

{# This macro tests that a column does not contain negative values #}
{# Returns failing records for dbt test framework #}

select
    *
from {{ model }}
where {{ column_name }} < 0

{% endmacro %}
```

#### macros/testing/test_date_range.sql

```sql
{% macro test_date_range(model, column_name, min_date, max_date) %}

{# This macro tests that dates fall within an expected range #}
{# Returns failing records for dbt test framework #}

select
    *
from {{ model }}
where {{ column_name }} < {{ min_date }}
   or {{ column_name }} > {{ max_date }}

{% endmacro %}
```

## Using Macros in Models

Macros can be called from models to implement reusable logic:

```sql
-- Example model using macros
with orders as (
    select * from {{ ref('stg_orders') }}
),

customers as (
    select * from {{ ref('stg_customers') }}
),

-- Calculate customer metrics
customer_metrics as (
    select
        customer_id,
        count(order_id) as order_count,
        {{ calculate_customer_ltv('customer_id', 'total_amount', 'is_cancelled') }} as lifetime_value,
        {{ categorize_customer('order_count', 'lifetime_value') }} as customer_segment
    from orders
    group by 1
)

select * from customer_metrics
```

## Macro Best Practices

1. **Documentation**:
   - Document macro purpose and parameters
   - Include examples of usage
   - Explain any assumptions or limitations

2. **Modularity**:
   - Keep macros focused on a single responsibility
   - Break complex logic into smaller macros
   - Use parameters for flexibility

3. **Error Handling**:
   - Handle edge cases and null values
   - Provide meaningful error messages
   - Use safe operations where appropriate

4. **Performance**:
   - Consider query performance implications
   - Optimize for BigQuery when necessary
   - Test with representative data volumes

5. **Reusability**:
   - Design macros to be reusable across models
   - Use parameters instead of hardcoding values
   - Consider creating a package for widely used macros

6. **Naming Conventions**:
   - Use clear, descriptive names
   - Follow a consistent naming pattern
   - Group related macros in subdirectories

## Macro Directory Structure

```
macros/
├── utils/
│   ├── date_spine.sql
│   ├── safe_divide.sql
│   └── generate_surrogate_key.sql
├── business_logic/
│   ├── calculate_customer_ltv.sql
│   ├── calculate_product_margin.sql
│   └── categorize_customer.sql
├── bigquery/
│   ├── partition_by.sql
│   ├── cluster_by.sql
│   └── create_temp_table.sql
└── testing/
    ├── test_not_negative.sql
    └── test_date_range.sql
```

## Macro Documentation

Create a `macros/macros.md` file to document your macros:

```markdown
{% docs macros_overview %}

# Macros Overview

This project includes the following macro categories:

## Utility Macros

General-purpose helpers for common operations:
- `date_spine`: Generates a date spine between start_date and end_date
- `safe_divide`: Safely handles division by zero
- `generate_surrogate_key`: Generates a surrogate key from a list of fields

## Business Logic Macros

Encapsulate specific business calculations:
- `calculate_customer_ltv`: Calculates customer lifetime value
- `calculate_product_margin`: Calculates product margin percentage
- `categorize_customer`: Categorizes customers based on order count and lifetime value

## BigQuery-Specific Macros

Optimizations for BigQuery:
- `partition_by`: Generates BigQuery partition by clause
- `cluster_by`: Generates BigQuery cluster by clause
- `create_temp_table`: Creates a temporary table in BigQuery

## Testing Macros

Custom test logic for data validation:
- `test_not_negative`: Tests that a column does not contain negative values
- `test_date_range`: Tests that dates fall within an expected range

{% enddocs %}