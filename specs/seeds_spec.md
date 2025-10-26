# Seeds Specification

Seeds in dbt are CSV files that can be loaded as tables in your data warehouse. They are useful for static reference data that doesn't change frequently, such as country codes, product categories, or mapping tables. For an e-commerce analytics project on BigQuery, seeds can provide valuable reference data that enhances your models.

## Purpose of Seeds

1. **Reference Data**: Static lookup tables that don't change frequently
2. **Mapping Tables**: Mappings between codes and descriptions
3. **Test Data**: Sample data for testing models
4. **Configuration Data**: Parameters and settings for models

## Example Seed Files

### 1. Country Codes

#### seeds/country_codes.csv

```csv
country_code,country_name,continent,region
US,United States,North America,North America
CA,Canada,North America,North America
MX,Mexico,North America,Latin America
GB,United Kingdom,Europe,Western Europe
DE,Germany,Europe,Western Europe
FR,France,Europe,Western Europe
IT,Italy,Europe,Southern Europe
ES,Spain,Europe,Southern Europe
JP,Japan,Asia,East Asia
CN,China,Asia,East Asia
IN,India,Asia,South Asia
AU,Australia,Oceania,Oceania
BR,Brazil,South America,Latin America
AR,Argentina,South America,Latin America
ZA,South Africa,Africa,Southern Africa
NG,Nigeria,Africa,Western Africa
```

### 2. Product Categories

#### seeds/product_categories.csv

```csv
category_id,parent_category_id,category_name,category_description,category_level
1,,Electronics,Electronic devices and accessories,1
2,1,Computers,Desktop and laptop computers,2
3,1,Mobile Phones,Smartphones and mobile devices,2
4,1,Audio,Headphones and speakers,2
5,1,Accessories,Electronic accessories,2
6,,Clothing,Apparel and fashion items,1
7,6,Men's Clothing,Clothing for men,2
8,6,Women's Clothing,Clothing for women,2
9,6,Children's Clothing,Clothing for children,2
10,6,Accessories,Fashion accessories,2
11,,Home,Home goods and furniture,1
12,11,Furniture,Tables, chairs, and other furniture,2
13,11,Kitchen,Kitchen appliances and utensils,2
14,11,Bedding,Bedding and linens,2
15,11,Decor,Home decoration items,2
```

### 3. Shipping Methods

#### seeds/shipping_methods.csv

```csv
shipping_method_id,shipping_method_name,shipping_method_description,estimated_days_min,estimated_days_max,base_cost
1,Standard,Standard shipping (5-7 business days),5,7,4.99
2,Express,Express shipping (2-3 business days),2,3,9.99
3,Next Day,Next day delivery (1 business day),1,1,19.99
4,Same Day,Same day delivery (select areas only),0,0,29.99
5,Free,Free standard shipping (7-10 business days),7,10,0.00
```

### 4. Payment Methods

#### seeds/payment_methods.csv

```csv
payment_method_id,payment_method_name,payment_method_type,is_active
1,Credit Card,credit,true
2,Debit Card,debit,true
3,PayPal,digital,true
4,Apple Pay,digital,true
5,Google Pay,digital,true
6,Bank Transfer,bank,true
7,Gift Card,gift,true
8,Store Credit,credit,true
9,Cash on Delivery,cash,false
10,Cryptocurrency,digital,false
```

### 5. Order Status Definitions

#### seeds/order_status_definitions.csv

```csv
status_code,status_name,status_description,is_cancelled,is_completed,is_returned,display_order
pending,Pending,Order has been placed but not yet processed,false,false,false,1
processing,Processing,Order is being processed,false,false,false,2
shipped,Shipped,Order has been shipped,false,false,false,3
delivered,Delivered,Order has been delivered,false,true,false,4
cancelled,Cancelled,Order has been cancelled,true,false,false,5
returned,Returned,Order has been returned,false,true,true,6
refunded,Refunded,Order has been refunded,true,true,false,7
on_hold,On Hold,Order is on hold,false,false,false,8
```

### 6. Marketing Campaign Types

#### seeds/marketing_campaign_types.csv

```csv
campaign_type_id,campaign_type_name,campaign_type_description,channel,is_active
1,Email Newsletter,Regular email newsletter to subscribers,email,true
2,Promotional Email,Special promotional emails,email,true
3,Social Media Ads,Paid social media advertising,social,true
4,Search Engine Ads,Paid search engine advertising,search,true
5,Display Ads,Display advertising on websites,display,true
6,Affiliate Marketing,Marketing through affiliate partners,affiliate,true
7,Influencer Marketing,Marketing through influencers,social,true
8,Content Marketing,Marketing through content creation,content,true
9,SMS Marketing,Marketing through text messages,sms,true
10,Push Notifications,Marketing through app notifications,mobile,true
```

## Configuring Seeds

Seeds can be configured in the `dbt_project.yml` file:

```yaml
seeds:
  ecommerce_analytics:
    +schema: reference_data
    +quote_columns: true
    
    # Specific configurations for individual seeds
    country_codes:
      +column_types:
        country_code: string
        country_name: string
        continent: string
        region: string
    
    product_categories:
      +column_types:
        category_id: integer
        parent_category_id: integer
        category_name: string
        category_description: string
        category_level: integer
```

## Documenting Seeds

Seeds can be documented in a `seeds/schema.yml` file:

```yaml
version: 2

seeds:
  - name: country_codes
    description: "Reference table for country codes and names"
    columns:
      - name: country_code
        description: "ISO 3166-1 alpha-2 country code"
        tests:
          - unique
          - not_null
      - name: country_name
        description: "Country name"
        tests:
          - not_null
      - name: continent
        description: "Continent name"
        tests:
          - not_null
      - name: region
        description: "Geographic region"
        tests:
          - not_null

  - name: product_categories
    description: "Product category hierarchy"
    columns:
      - name: category_id
        description: "Primary key for product categories"
        tests:
          - unique
          - not_null
      - name: parent_category_id
        description: "Foreign key to parent category (null for top-level categories)"
      - name: category_name
        description: "Category name"
        tests:
          - not_null
      - name: category_description
        description: "Category description"
      - name: category_level
        description: "Hierarchy level (1 for top-level, 2 for second-level, etc.)"
        tests:
          - not_null
```

## Seed Best Practices

1. **Use Seeds Appropriately**:
   - Only use seeds for static reference data
   - Avoid using seeds for large datasets
   - Consider other options for frequently changing data

2. **Version Control**:
   - Keep seeds in version control
   - Document changes to seeds
   - Consider using a change log

3. **Data Quality**:
   - Validate seed data before committing
   - Include tests for seed data
   - Ensure consistent formatting

4. **Documentation**:
   - Document the purpose of each seed
   - Document the source of the data
   - Document any transformations applied

5. **Organization**:
   - Use consistent naming conventions
   - Group related seeds together
   - Consider subdirectories for organization

## Using Seeds in Models

Seeds can be referenced in models using the `ref()` function:

```sql
with country_codes as (
    select * from {{ ref('country_codes') }}
),

customer_orders as (
    select * from {{ ref('fact_orders') }}
),

-- Join customer orders with country codes
customer_orders_with_country as (
    select
        co.*,
        cc.country_name,
        cc.continent,
        cc.region
    from customer_orders co
    left join country_codes cc on co.country_code = cc.country_code
)

select * from customer_orders_with_country
```

## Seed Directory Structure

```
seeds/
├── schema.yml                      # Documentation for seeds
├── country_codes.csv               # Country reference data
├── product_categories.csv          # Product category hierarchy
├── shipping_methods.csv            # Shipping method reference data
├── payment_methods.csv             # Payment method reference data
├── order_status_definitions.csv    # Order status definitions
└── marketing_campaign_types.csv    # Marketing campaign type definitions
```

## Seed Documentation

Create a `seeds/README.md` file to document your seeds:

```markdown
# Seeds

This directory contains CSV files that are loaded as tables in the data warehouse. These files contain static reference data that doesn't change frequently.

## Country Codes

`country_codes.csv` contains ISO 3166-1 alpha-2 country codes, country names, continents, and regions. This data is used for geographic analysis and reporting.

## Product Categories

`product_categories.csv` contains the product category hierarchy. This data is used for product classification and reporting.

## Shipping Methods

`shipping_methods.csv` contains shipping method definitions, including estimated delivery times and base costs.

## Payment Methods

`payment_methods.csv` contains payment method definitions, including payment types and active status.

## Order Status Definitions

`order_status_definitions.csv` contains order status definitions, including descriptions and flags for cancelled, completed, and returned orders.

## Marketing Campaign Types

`marketing_campaign_types.csv` contains marketing campaign type definitions, including channels and active status.