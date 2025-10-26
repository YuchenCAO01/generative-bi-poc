# profiles.yml Specification

This file contains the connection configuration for your dbt project. Below is the recommended content for a BigQuery e-commerce analytics project:

```yaml
# This file should be stored in ~/.dbt/ directory
# Do not commit this file to version control with credentials

ecommerce_analytics:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: oauth  # or service-account
      project: your-gcp-project-id  # GCP project ID
      dataset: ecommerce_analytics_dev  # Default BigQuery dataset
      threads: 4  # Number of concurrent connections
      timeout_seconds: 300  # Query timeout
      location: US  # BigQuery dataset location
      priority: interactive  # or batch
      retries: 3  # Number of retries for failed queries
      
      # If using service account authentication
      # keyfile: /path/to/keyfile.json
      
      # If using impersonated service account
      # impersonate_service_account: service-account@project.iam.gserviceaccount.com
      
    prod:
      type: bigquery
      method: oauth  # or service-account
      project: your-gcp-project-id  # GCP project ID
      dataset: ecommerce_analytics_prod  # Default BigQuery dataset
      threads: 8  # Number of concurrent connections
      timeout_seconds: 300  # Query timeout
      location: US  # BigQuery dataset location
      priority: interactive  # or batch
      retries: 3  # Number of retries for failed queries
      
      # If using service account authentication
      # keyfile: /path/to/keyfile.json
      
      # If using impersonated service account
      # impersonate_service_account: service-account@project.iam.gserviceaccount.com
    
    ci:
      type: bigquery
      method: oauth  # or service-account
      project: your-gcp-project-id  # GCP project ID
      dataset: ecommerce_analytics_ci  # Default BigQuery dataset
      threads: 4  # Number of concurrent connections
      timeout_seconds: 300  # Query timeout
      location: US  # BigQuery dataset location
      priority: interactive  # or batch
      retries: 3  # Number of retries for failed queries
```

## Key Configuration Elements

1. **Profile Name**:
   - `ecommerce_analytics` - Must match the profile name in dbt_project.yml

2. **Default Target**:
   - `target: dev` - The default environment to use

3. **Environment Configurations**:
   - `dev` - Development environment
   - `prod` - Production environment
   - `ci` - Continuous Integration environment

4. **BigQuery Connection Parameters**:
   - `type: bigquery` - Specifies BigQuery as the adapter
   - `method: oauth` - Authentication method (oauth or service-account)
   - `project` - GCP project ID
   - `dataset` - Default BigQuery dataset
   - `threads` - Number of concurrent connections
   - `timeout_seconds` - Query timeout
   - `location` - BigQuery dataset location
   - `priority` - Query priority (interactive or batch)
   - `retries` - Number of retries for failed queries

5. **Authentication Options**:
   - OAuth (default for local development)
   - Service Account (recommended for production)
   - Impersonated Service Account (for enhanced security)

## Security Considerations

1. **Never commit profiles.yml with credentials to version control**
2. **Store the file in ~/.dbt/ directory**
3. **Use environment variables for sensitive information**:
   ```yaml
   keyfile: "{{ env_var('DBT_KEYFILE_PATH') }}"
   project: "{{ env_var('DBT_PROJECT_ID') }}"
   ```
4. **Consider using a secrets manager for production deployments**

## Environment-Specific Configurations

Different environments may require different configurations:

1. **Development**:
   - Fewer threads
   - Smaller dataset
   - OAuth authentication

2. **Production**:
   - More threads for performance
   - Service account authentication
   - Possibly different project/dataset

3. **CI/CD**:
   - Service account authentication
   - Temporary dataset
   - Possibly different project