# Data Quality Tests Specification

Data quality tests are a critical component of a dbt project, ensuring that your data meets expected standards and business rules. dbt provides both built-in tests and the ability to create custom tests for more complex validation.

## Types of dbt Tests

1. **Schema Tests**: Simple, declarative tests defined in YAML files
2. **Singular Tests**: Custom SQL queries that return failing records
3. **Data Tests**: Tests that validate entire datasets or complex business rules

## Example Test Files

### 1. Schema Tests in YAML

Schema tests are defined in YAML files alongside model definitions. They can be applied to columns or relationships between models.

#### models/staging/schema.yml

```yaml
version: 2

models:
  - name: stg_customers
    description: "Cleaned customer data from the raw customers table"
    columns:
      - name: customer_id
        description: "The primary key for customers"
        tests:
          - unique
          - not_null
      - name: email
        description: "Customer email address"
        tests:
          - not_null
          - unique
      - name: created_at
        description: "Timestamp when customer was created"
        tests:
          - not_null

  - name: stg_orders
    description: "Cleaned order data from the raw orders table"
    columns:
      - name: order_id
        description: "The primary key for orders"
        tests:
          - unique
          - not_null
      - name: customer_id
        description: "Foreign key to customers"
        tests:
          - not_null
          - relationships:
              to: ref('stg_customers')
              field: customer_id
      - name: order_status
        description: "Current order status"
        tests:
          - not_null
          - accepted_values:
              values: ['pending', 'processing', 'shipped', 'delivered', 'cancelled', 'returned']
```

### 2. Custom Generic Tests

Custom generic tests can be created for reusable testing patterns.

#### tests/generic/test_positive_values.sql

```sql
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
```

#### tests/generic/test_date_in_past.sql

```sql
{% test date_in_past(model, column_name) %}

with validation as (
    select
        {{ column_name }} as date_field
    from {{ model }}
    where {{ column_name }} > current_date()
)

select *
from validation

{% endtest %}
```

### 3. Singular Tests

Singular tests are SQL queries that return failing records.

#### tests/assert_total_amount_equals_sum_of_items.sql

```sql
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
```

#### tests/assert_no_future_order_dates.sql

```sql
-- Test that no orders have future dates
select
    order_id,
    order_date
from {{ ref('fact_orders') }}
where order_date > current_date()
```

### 4. Using the tests in models

After defining custom generic tests, you can use them in your schema files:

```yaml
version: 2

models:
  - name: fact_orders
    description: "Order fact table at the order header level"
    columns:
      - name: order_id
        description: "The primary key for the order fact table"
        tests:
          - unique
          - not_null
      - name: total_amount
        description: "Total order amount"
        tests:
          - not_null
          - positive_values  # Custom generic test
```

## Comprehensive Testing Strategy

A comprehensive testing strategy for an e-commerce analytics project should include:

### 1. Source Data Tests

Test raw data quality and freshness:

```yaml
version: 2

sources:
  - name: ecommerce_raw
    database: your-gcp-project-id
    schema: raw_data
    tables:
      - name: customers
        columns:
          - name: customer_id
            tests:
              - unique
              - not_null
        freshness:
          warn_after:
            count: 24
            period: hour
          error_after:
            count: 48
            period: hour
```

### 2. Staging Model Tests

Test data cleaning and basic integrity:

```yaml
version: 2

models:
  - name: stg_customers
    columns:
      - name: customer_id
        tests:
          - unique
          - not_null
      - name: email
        tests:
          - not_null
          - unique
```

### 3. Intermediate Model Tests

Test business logic and transformations:

```yaml
version: 2

models:
  - name: int_customer_orders
    columns:
      - name: customer_id
        tests:
          - unique
          - not_null
      - name: lifetime_value
        tests:
          - not_null
          - positive_values
```

### 4. Dimensional Model Tests

Test relationships and aggregations:

```yaml
version: 2

models:
  - name: dim_customers
    columns:
      - name: customer_id
        tests:
          - unique
          - not_null
  
  - name: fact_orders
    columns:
      - name: order_id
        tests:
          - unique
          - not_null
      - name: customer_id
        tests:
          - not_null
          - relationships:
              to: ref('dim_customers')
              field: customer_id
```

### 5. Business Rule Tests

Test complex business rules with singular tests:

```sql
-- tests/assert_customer_lifetime_value_matches_orders.sql
with customer_ltv as (
    select
        customer_id,
        lifetime_value
    from {{ ref('dim_customers') }}
),

order_totals as (
    select
        customer_id,
        sum(total_amount) as total_order_amount
    from {{ ref('fact_orders') }}
    where is_cancelled = false
    group by 1
),

validation as (
    select
        c.customer_id,
        c.lifetime_value,
        o.total_order_amount,
        abs(c.lifetime_value - o.total_order_amount) as difference
    from customer_ltv c
    inner join order_totals o on c.customer_id = o.customer_id
    where abs(c.lifetime_value - o.total_order_amount) > 0.01
)

select *
from validation
```

## Test Configuration

Configure test behavior in `dbt_project.yml`:

```yaml
tests:
  +store_failures: true
  +schema: test_failures
  +severity: error  # or warn
  
  ecommerce_analytics:
    +severity: error
    
    staging:
      +severity: warn
```

## Test Best Practices

1. **Test Coverage**:
   - Test all primary and foreign keys
   - Test critical business calculations
   - Test important business rules

2. **Test Organization**:
   - Organize tests alongside models
   - Use consistent naming conventions
   - Document test purpose and expectations

3. **Test Performance**:
   - Configure test materialization for large datasets
   - Use appropriate limits for development testing
   - Consider performance impact in CI/CD pipelines

4. **Test Maintenance**:
   - Review and update tests when models change
   - Remove obsolete tests
   - Document known limitations

5. **Test Severity**:
   - Use appropriate severity levels (warn vs. error)
   - Configure critical tests to block deployments
   - Consider business impact when setting severity

## Test Directory Structure

```
models/
├── staging/
│   └── schema.yml           # Tests for staging models
├── intermediate/
│   └── schema.yml           # Tests for intermediate models
├── dimensions/
│   └── schema.yml           # Tests for dimension models
├── facts/
│   └── schema.yml           # Tests for fact models
└── marts/
    └── schema.yml           # Tests for mart models

tests/
├── generic/
│   ├── test_positive_values.sql
│   └── test_date_in_past.sql
└── singular/
    ├── assert_total_amount_equals_sum_of_items.sql
    └── assert_no_future_order_dates.sql