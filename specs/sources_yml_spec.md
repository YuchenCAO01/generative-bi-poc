# Sources YAML Specification

This file defines the raw data sources for your dbt project. For an e-commerce analytics project on BigQuery, you would typically place this in `models/staging/sources.yml`.

```yaml
version: 2

sources:
  - name: ecommerce_raw
    database: your-gcp-project-id  # GCP project ID
    schema: raw_data  # BigQuery dataset containing raw data
    description: "Raw e-commerce data from operational systems"
    
    # Freshness checks to ensure data is being loaded properly
    freshness:
      warn_after:
        count: 12
        period: hour
      error_after:
        count: 24
        period: hour
    
    # Loader information
    loader: "Fivetran"  # or other data loading tool
    
    # List of tables in this source
    tables:
      - name: customers
        description: "Customer information including demographics and account details"
        columns:
          - name: customer_id
            description: "Primary key for customers"
            tests:
              - unique
              - not_null
          - name: email
            description: "Customer email address"
            tests:
              - not_null
          - name: first_name
            description: "Customer first name"
          - name: last_name
            description: "Customer last name"
          - name: created_at
            description: "Timestamp when customer was created"
            tests:
              - not_null
          - name: updated_at
            description: "Timestamp when customer was last updated"
        
        # Table-specific freshness checks
        freshness:
          warn_after:
            count: 24
            period: hour
          error_after:
            count: 48
            period: hour
      
      - name: products
        description: "Product catalog information"
        columns:
          - name: product_id
            description: "Primary key for products"
            tests:
              - unique
              - not_null
          - name: name
            description: "Product name"
            tests:
              - not_null
          - name: description
            description: "Product description"
          - name: category_id
            description: "Foreign key to product categories"
            tests:
              - not_null
              - relationships:
                  to: source('ecommerce_raw', 'product_categories')
                  field: category_id
          - name: price
            description: "Current product price"
            tests:
              - not_null
          - name: created_at
            description: "Timestamp when product was created"
            tests:
              - not_null
          - name: updated_at
            description: "Timestamp when product was last updated"
      
      - name: product_categories
        description: "Product category hierarchy"
        columns:
          - name: category_id
            description: "Primary key for product categories"
            tests:
              - unique
              - not_null
          - name: name
            description: "Category name"
            tests:
              - not_null
          - name: parent_category_id
            description: "Self-referential foreign key to parent category"
            tests:
              - relationships:
                  to: source('ecommerce_raw', 'product_categories')
                  field: category_id
      
      - name: orders
        description: "Order header information"
        columns:
          - name: order_id
            description: "Primary key for orders"
            tests:
              - unique
              - not_null
          - name: customer_id
            description: "Foreign key to customers"
            tests:
              - not_null
              - relationships:
                  to: source('ecommerce_raw', 'customers')
                  field: customer_id
          - name: order_date
            description: "Date when order was placed"
            tests:
              - not_null
          - name: status
            description: "Current order status"
            tests:
              - not_null
              - accepted_values:
                  values: ['pending', 'processing', 'shipped', 'delivered', 'cancelled', 'returned']
          - name: total_amount
            description: "Total order amount"
            tests:
              - not_null
          - name: created_at
            description: "Timestamp when order was created"
            tests:
              - not_null
          - name: updated_at
            description: "Timestamp when order was last updated"
      
      - name: order_items
        description: "Order line items"
        columns:
          - name: order_item_id
            description: "Primary key for order items"
            tests:
              - unique
              - not_null
          - name: order_id
            description: "Foreign key to orders"
            tests:
              - not_null
              - relationships:
                  to: source('ecommerce_raw', 'orders')
                  field: order_id
          - name: product_id
            description: "Foreign key to products"
            tests:
              - not_null
              - relationships:
                  to: source('ecommerce_raw', 'products')
                  field: product_id
          - name: quantity
            description: "Quantity ordered"
            tests:
              - not_null
          - name: unit_price
            description: "Price at time of order"
            tests:
              - not_null
          - name: created_at
            description: "Timestamp when order item was created"
            tests:
              - not_null
          - name: updated_at
            description: "Timestamp when order item was last updated"
      
      - name: inventory
        description: "Product inventory levels"
        columns:
          - name: inventory_id
            description: "Primary key for inventory records"
            tests:
              - unique
              - not_null
          - name: product_id
            description: "Foreign key to products"
            tests:
              - not_null
              - relationships:
                  to: source('ecommerce_raw', 'products')
                  field: product_id
          - name: warehouse_id
            description: "Foreign key to warehouses"
            tests:
              - not_null
          - name: quantity_on_hand
            description: "Current inventory quantity"
            tests:
              - not_null
          - name: created_at
            description: "Timestamp when inventory record was created"
            tests:
              - not_null
          - name: updated_at
            description: "Timestamp when inventory record was last updated"
      
      - name: marketing_campaigns
        description: "Marketing campaign information"
        columns:
          - name: campaign_id
            description: "Primary key for marketing campaigns"
            tests:
              - unique
              - not_null
          - name: name
            description: "Campaign name"
            tests:
              - not_null
          - name: type
            description: "Campaign type"
            tests:
              - not_null
              - accepted_values:
                  values: ['email', 'social', 'search', 'display', 'affiliate']
          - name: start_date
            description: "Campaign start date"
            tests:
              - not_null
          - name: end_date
            description: "Campaign end date"
          - name: budget
            description: "Campaign budget"
            tests:
              - not_null
          - name: created_at
            description: "Timestamp when campaign was created"
            tests:
              - not_null
          - name: updated_at
            description: "Timestamp when campaign was last updated"
      
      - name: website_events
        description: "Website user interaction events"
        columns:
          - name: event_id
            description: "Primary key for website events"
            tests:
              - unique
              - not_null
          - name: session_id
            description: "Website session identifier"
            tests:
              - not_null
          - name: customer_id
            description: "Foreign key to customers (null for anonymous users)"
            tests:
              - relationships:
                  to: source('ecommerce_raw', 'customers')
                  field: customer_id
          - name: event_type
            description: "Type of website event"
            tests:
              - not_null
              - accepted_values:
                  values: ['page_view', 'product_view', 'add_to_cart', 'remove_from_cart', 'checkout', 'purchase']
          - name: product_id
            description: "Foreign key to products (for product-related events)"
            tests:
              - relationships:
                  to: source('ecommerce_raw', 'products')
                  field: product_id
          - name: page_url
            description: "URL of the page where the event occurred"
            tests:
              - not_null
          - name: device_type
            description: "Type of device used"
            tests:
              - accepted_values:
                  values: ['desktop', 'mobile', 'tablet']
          - name: created_at
            description: "Timestamp when event occurred"
            tests:
              - not_null
```

## Key Configuration Elements

1. **Source Definition**:
   - `name: ecommerce_raw` - The name of the source
   - `database` - GCP project ID
   - `schema` - BigQuery dataset containing raw data
   - `description` - Description of the source

2. **Freshness Checks**:
   - Define how fresh the data should be
   - Set warning and error thresholds
   - Can be defined at source or table level

3. **Table Definitions**:
   - List of tables in the source
   - Descriptions for each table
   - Column definitions with descriptions

4. **Data Quality Tests**:
   - Primary key tests (unique, not_null)
   - Foreign key tests (relationships)
   - Value validation tests (accepted_values)
   - Custom tests can be added

5. **Documentation**:
   - Descriptions for sources, tables, and columns
   - Business context for the data

## Best Practices

1. **Comprehensive Documentation**:
   - Document all sources, tables, and columns
   - Include business context and data lineage

2. **Robust Testing**:
   - Test primary and foreign keys
   - Validate value domains
   - Check for data freshness

3. **Consistent Naming**:
   - Use consistent naming conventions
   - Follow the same pattern for all sources

4. **Modular Organization**:
   - Consider splitting large sources.yml files
   - Organize by business domain or data source