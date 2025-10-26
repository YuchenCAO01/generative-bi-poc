# Staging Models Specification

Staging models are the first transformation layer in the dbt project. They perform minimal transformations on raw data, focusing on cleaning, renaming, and type casting. For an e-commerce analytics project on BigQuery, these models would be placed in the `models/staging/` directory.

## Staging Model Structure

Each staging model should follow this general pattern:

```sql
with source as (
    select * from {{ source('ecommerce_raw', 'table_name') }}
),

renamed as (
    select
        -- Primary keys
        id as table_name_id,
        
        -- Foreign keys
        related_id as related_table_id,
        
        -- Regular fields with consistent naming
        field_1 as renamed_field_1,
        field_2 as renamed_field_2,
        
        -- Type casting examples
        cast(numeric_field as numeric) as numeric_field,
        cast(timestamp_field as timestamp) as timestamp_field,
        
        -- Boolean conversions
        case
            when status = 'active' then true
            else false
        end as is_active,
        
        -- Add standardized audit fields
        created_at,
        updated_at,
        
        -- Add metadata fields
        '{{ invocation_id }}' as _invocation_id,
        current_timestamp() as _loaded_at
    from source
)

select * from renamed
```

## Example Staging Models

### 1. stg_customers.sql

```sql
with source as (
    select * from {{ source('ecommerce_raw', 'customers') }}
),

renamed as (
    select
        -- Primary key
        customer_id,
        
        -- Customer attributes
        email,
        first_name,
        last_name,
        
        -- Combine fields
        concat(first_name, ' ', last_name) as full_name,
        
        -- Type casting
        safe_cast(created_at as timestamp) as created_at,
        safe_cast(updated_at as timestamp) as updated_at,
        
        -- Add metadata fields
        '{{ invocation_id }}' as _invocation_id,
        current_timestamp() as _loaded_at
    from source
)

select * from renamed
```

### 2. stg_products.sql

```sql
with source as (
    select * from {{ source('ecommerce_raw', 'products') }}
),

renamed as (
    select
        -- Primary key
        product_id,
        
        -- Foreign keys
        category_id,
        
        -- Product attributes
        name as product_name,
        description as product_description,
        
        -- Type casting
        safe_cast(price as numeric) as price,
        safe_cast(created_at as timestamp) as created_at,
        safe_cast(updated_at as timestamp) as updated_at,
        
        -- Add metadata fields
        '{{ invocation_id }}' as _invocation_id,
        current_timestamp() as _loaded_at
    from source
)

select * from renamed
```

### 3. stg_orders.sql

```sql
with source as (
    select * from {{ source('ecommerce_raw', 'orders') }}
),

renamed as (
    select
        -- Primary key
        order_id,
        
        -- Foreign keys
        customer_id,
        
        -- Order attributes
        safe_cast(order_date as date) as order_date,
        status as order_status,
        
        -- Type casting
        safe_cast(total_amount as numeric) as total_amount,
        
        -- Derived fields
        case
            when status = 'cancelled' then true
            else false
        end as is_cancelled,
        
        case
            when status = 'delivered' then true
            else false
        end as is_delivered,
        
        -- Timestamps
        safe_cast(created_at as timestamp) as created_at,
        safe_cast(updated_at as timestamp) as updated_at,
        
        -- Add metadata fields
        '{{ invocation_id }}' as _invocation_id,
        current_timestamp() as _loaded_at
    from source
)

select * from renamed
```

### 4. stg_order_items.sql

```sql
with source as (
    select * from {{ source('ecommerce_raw', 'order_items') }}
),

renamed as (
    select
        -- Primary key
        order_item_id,
        
        -- Foreign keys
        order_id,
        product_id,
        
        -- Order item attributes
        quantity,
        
        -- Type casting
        safe_cast(unit_price as numeric) as unit_price,
        
        -- Derived fields
        safe_cast(quantity * unit_price as numeric) as item_total,
        
        -- Timestamps
        safe_cast(created_at as timestamp) as created_at,
        safe_cast(updated_at as timestamp) as updated_at,
        
        -- Add metadata fields
        '{{ invocation_id }}' as _invocation_id,
        current_timestamp() as _loaded_at
    from source
)

select * from renamed
```

### 5. stg_website_events.sql

```sql
with source as (
    select * from {{ source('ecommerce_raw', 'website_events') }}
),

renamed as (
    select
        -- Primary key
        event_id,
        
        -- Foreign keys
        session_id,
        customer_id,
        product_id,
        
        -- Event attributes
        event_type,
        page_url,
        device_type,
        
        -- Derived fields
        case
            when event_type = 'purchase' then true
            else false
        end as is_purchase_event,
        
        case
            when event_type = 'add_to_cart' then true
            else false
        end as is_add_to_cart_event,
        
        -- Extract page path from URL
        regexp_extract(page_url, r'^https?://[^/]+(/[^?#]*)') as page_path,
        
        -- Timestamps
        safe_cast(created_at as timestamp) as created_at,
        
        -- Add metadata fields
        '{{ invocation_id }}' as _invocation_id,
        current_timestamp() as _loaded_at
    from source
)

select * from renamed
```

## Staging Models Best Practices

1. **Minimal Transformations**:
   - Focus on cleaning, renaming, and type casting
   - Avoid complex business logic at this stage
   - Ensure consistent naming conventions

2. **Comprehensive Documentation**:
   - Document all models and columns
   - Include business context where relevant

3. **Type Safety**:
   - Use `safe_cast()` to prevent query failures
   - Handle null values appropriately

4. **Consistent Naming Conventions**:
   - Use singular nouns for table names (e.g., `stg_customer` not `stg_customers`)
   - Use suffixes for IDs (e.g., `customer_id` not just `customer`)
   - Use prefixes for boolean fields (e.g., `is_active` not just `active`)

5. **Metadata Fields**:
   - Include invocation ID for debugging
   - Add load timestamp for auditing

6. **Testing**:
   - Add schema tests for primary keys
   - Test for null values in required fields
   - Test relationships between models

## Schema.yml for Staging Models

Create a `models/staging/schema.yml` file to document and test the staging models:

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
      # Additional columns...

  - name: stg_products
    description: "Cleaned product data from the raw products table"
    columns:
      - name: product_id
        description: "The primary key for products"
        tests:
          - unique
          - not_null
      # Additional columns...

  # Additional models...
```

## Staging Models Directory Structure

```
models/
└── staging/
    ├── schema.yml
    ├── stg_customers.sql
    ├── stg_products.sql
    ├── stg_product_categories.sql
    ├── stg_orders.sql
    ├── stg_order_items.sql
    ├── stg_inventory.sql
    ├── stg_marketing_campaigns.sql
    └── stg_website_events.sql