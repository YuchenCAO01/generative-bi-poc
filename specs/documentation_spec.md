# Documentation Specification

Documentation is a critical component of a dbt project, making it easier for users to understand the data models, their relationships, and business context. dbt provides built-in documentation capabilities that can be leveraged to create comprehensive documentation for your project.

## Documentation Structure

dbt documentation consists of several components:

1. **Model Descriptions**: Descriptions of models, columns, and tests in YAML files
2. **Documentation Blocks**: Markdown files with detailed explanations
3. **Project Overview**: README files and project-level documentation
4. **Lineage Graphs**: Automatically generated visualizations of model dependencies

## Example Documentation Files

### 1. models/overview.md

```markdown
{% docs __overview__ %}

# E-commerce Analytics dbt Project

This dbt project transforms raw e-commerce data into analytics-ready models for reporting and analysis. The project follows a layered architecture:

## Data Flow

1. **Source Layer**: Raw data from operational systems
2. **Staging Layer**: Cleaned and standardized data
3. **Intermediate Layer**: Business logic and transformations
4. **Dimensional Layer**: Fact and dimension tables in a star schema
5. **Mart Layer**: Business-specific reporting models

## Business Domains

The project covers the following business domains:

- **Sales**: Order and product performance analysis
- **Customers**: Customer behavior and segmentation
- **Marketing**: Campaign performance and ROI analysis
- **Inventory**: Stock levels and product availability

## Getting Started

To use this project:

1. Configure your `profiles.yml` file with BigQuery credentials
2. Run `dbt deps` to install dependencies
3. Run `dbt build` to build all models and run tests
4. Run `dbt docs generate` to generate documentation
5. Run `dbt docs serve` to view documentation locally

{% enddocs %}
```

### 2. models/staging/staging.md

```markdown
{% docs staging_models %}

# Staging Models

Staging models perform minimal transformations on raw data, focusing on cleaning, renaming, and type casting. These models serve as a buffer between raw data and business logic.

## Naming Convention

Staging models follow the naming convention `stg_<source>_<entity>`, for example:
- `stg_customers`
- `stg_orders`
- `stg_products`

## Transformation Rules

Staging models apply the following transformations:
- Rename columns to follow a consistent naming convention
- Cast data types appropriately
- Handle null values
- Add metadata fields for auditing

## Example

```sql
with source as (
    select * from {{ source('ecommerce_raw', 'customers') }}
),

renamed as (
    select
        customer_id,
        email,
        first_name,
        last_name,
        concat(first_name, ' ', last_name) as full_name,
        safe_cast(created_at as timestamp) as created_at,
        safe_cast(updated_at as timestamp) as updated_at,
        '{{ invocation_id }}' as _invocation_id,
        current_timestamp() as _loaded_at
    from source
)

select * from renamed
```

{% enddocs %}
```

### 3. models/marts/marts.md

```markdown
{% docs mart_models %}

# Mart Models

Mart models are the final layer in the dbt project, designed specifically for reporting and analytics use cases. They combine facts and dimensions into business-specific models that are optimized for specific analytical domains.

## Organization

Mart models are organized by business domain:
- `marts/marketing/`: Marketing analytics models
- `marts/sales/`: Sales performance models
- `marts/customers/`: Customer behavior models

## Design Principles

Mart models follow these design principles:
- Denormalized for query performance
- Include all relevant dimension attributes
- Pre-calculate common metrics
- Optimized for specific reporting needs

## Example Use Cases

### Marketing Analytics

The `mart_campaign_performance` model can be used to:
- Analyze campaign ROI
- Compare performance across campaigns
- Track customer acquisition costs

### Sales Analytics

The `mart_sales_overview` model can be used to:
- Monitor daily/monthly sales trends
- Analyze product category performance
- Track order cancellation rates

### Customer Analytics

The `mart_customer_overview` model can be used to:
- Segment customers by value and frequency
- Analyze customer lifetime value
- Track customer retention and churn

{% enddocs %}
```

### 4. models/schema.yml with Documentation

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
      - name: full_name
        description: "Customer full name (first_name + last_name)"
      - name: created_at
        description: "Timestamp when customer was created"
        tests:
          - not_null
      - name: updated_at
        description: "Timestamp when customer was last updated"
      - name: _invocation_id
        description: "dbt invocation ID for debugging"
      - name: _loaded_at
        description: "Timestamp when record was loaded"
```

### 5. models/metrics.yml

```yaml
version: 2

metrics:
  - name: total_revenue
    label: Total Revenue
    model: ref('fact_orders')
    description: "Total order revenue"
    
    calculation_method: sum
    expression: total_amount
    
    dimensions:
      - order_date
      - customer_id
    
    filters:
      - field: is_cancelled
        operator: 'is'
        value: 'false'
    
    time_grains:
      - day
      - week
      - month
      - quarter
      - year

  - name: average_order_value
    label: Average Order Value
    model: ref('fact_orders')
    description: "Average value of orders"
    
    calculation_method: average
    expression: total_amount
    
    dimensions:
      - order_date
      - customer_id
    
    filters:
      - field: is_cancelled
        operator: 'is'
        value: 'false'
    
    time_grains:
      - day
      - week
      - month
      - quarter
      - year
```

## Documentation Best Practices

1. **Comprehensive Model Documentation**:
   - Document all models and columns
   - Include business context and definitions
   - Explain complex calculations and business rules

2. **Use Markdown for Readability**:
   - Format documentation with headers, lists, and code blocks
   - Include examples where helpful
   - Use tables for structured information

3. **Include Business Context**:
   - Explain the business purpose of models
   - Document business rules and assumptions
   - Include links to relevant business documentation

4. **Document Data Lineage**:
   - Explain data sources and transformations
   - Document dependencies between models
   - Include information about refresh schedules

5. **Keep Documentation Updated**:
   - Update documentation when models change
   - Review documentation regularly
   - Include version information

## Generating and Viewing Documentation

To generate and view dbt documentation:

1. **Generate Documentation**:
   ```bash
   dbt docs generate
   ```

2. **Serve Documentation Locally**:
   ```bash
   dbt docs serve
   ```

3. **Deploy Documentation**:
   - Host the generated documentation on a web server
   - Integrate with CI/CD pipelines to keep documentation updated
   - Consider using dbt Cloud for hosted documentation

## Documentation Directory Structure

```
models/
├── overview.md                  # Project overview documentation
├── schema.yml                   # Project-level schema definitions
├── metrics.yml                  # Project-level metric definitions
├── staging/
│   ├── schema.yml               # Staging model documentation
│   └── staging.md               # Staging layer documentation
├── intermediate/
│   ├── schema.yml               # Intermediate model documentation
│   └── intermediate.md          # Intermediate layer documentation
├── dimensions/
│   ├── schema.yml               # Dimension model documentation
│   └── dimensions.md            # Dimension layer documentation
├── facts/
│   ├── schema.yml               # Fact model documentation
│   └── facts.md                 # Fact layer documentation
└── marts/
    ├── marts.md                 # Mart layer documentation
    ├── marketing/
    │   └── schema.yml           # Marketing mart documentation
    ├── sales/
    │   └── schema.yml           # Sales mart documentation
    └── customers/
        └── schema.yml           # Customer mart documentation