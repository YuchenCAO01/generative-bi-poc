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