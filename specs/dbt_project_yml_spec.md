# dbt_project.yml Specification

This file will be the main configuration file for the dbt project. Below is the recommended content for a BigQuery e-commerce analytics project:

```yaml
name: 'ecommerce_analytics'
version: '1.0.0'
config-version: 2

# This setting configures which "profile" dbt uses for this project.
profile: 'ecommerce_analytics'

# These configurations specify where dbt should look for different types of files.
# The `model-paths` config, for example, states that models in this project can be
# found in the "models/" directory. You probably won't need to change these!
model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

target-path: "target"  # directory which will store compiled SQL files
clean-targets:         # directories to be removed by `dbt clean`
  - "target"
  - "dbt_packages"

# Configuring models
# Full documentation: https://docs.getdbt.com/docs/configuring-models

# In this example config, we tell dbt to build all models in the example/ directory
# as tables. These settings can be overridden in the individual model files
# using the `{{ config(...) }}` macro.
models:
  ecommerce_analytics:
    # Config indicated by + and applies to all files under models/
    +materialized: view
    +persist_docs:
      relation: true
      columns: true
    
    staging:
      +materialized: view
      +schema: staging
    
    intermediate:
      +materialized: view
      +schema: intermediate
    
    dimensions:
      +materialized: table
      +schema: dimensions
    
    facts:
      +materialized: incremental
      +schema: facts
      +incremental_strategy: merge
      +unique_key: id
    
    marts:
      +materialized: table
      +schema: marts

# Configuring seeds
seeds:
  ecommerce_analytics:
    +schema: reference_data
    +quote_columns: true

# Configuring snapshots
snapshots:
  ecommerce_analytics:
    +target_schema: snapshots
    +strategy: timestamp
    +updated_at: updated_at
    +unique_key: id

# Configuring tests
tests:
  +store_failures: true
  +schema: test_failures

# BigQuery specific configurations
vars:
  # BigQuery specific variables
  bigquery_partition_by: "DATE(created_at)"
  bigquery_cluster_by: "customer_id, order_id"
```

## Key Configuration Elements

1. **Project Name and Version**: 
   - `name: 'ecommerce_analytics'` - The project name
   - `version: '1.0.0'` - The project version

2. **Profile Configuration**:
   - `profile: 'ecommerce_analytics'` - References the profile in profiles.yml

3. **Directory Paths**:
   - Defines where dbt should look for different types of files

4. **Model Configurations**:
   - Default materialization strategies for different model types
   - Schema naming conventions
   - BigQuery-specific configurations like partitioning and clustering

5. **Seed Configurations**:
   - Schema for reference data
   - Column quoting behavior

6. **Snapshot Configurations**:
   - Target schema for snapshots
   - Strategy for tracking changes
   - Key fields for change detection

7. **Test Configurations**:
   - Storage of test failures
   - Schema for test results

8. **BigQuery Variables**:
   - Partitioning and clustering configurations
   - Other BigQuery-specific optimizations