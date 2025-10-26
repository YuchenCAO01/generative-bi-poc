{% macro create_datasets() %}
  
  {% set datasets = [
    target.schema ~ "_intermediate",
    target.schema ~ "_dimensions",
    target.schema ~ "_facts",
    target.schema ~ "_marts"
  ] %}
  
  {% for dataset in datasets %}
    {% set create_dataset_query %}
      CREATE SCHEMA IF NOT EXISTS `{{ target.project }}.{{ dataset }}`
      OPTIONS(location="australia-southeast2");
    {% endset %}
    
    {% do run_query(create_dataset_query) %}
    {{ log("Created dataset: " ~ target.project ~ "." ~ dataset, info=True) }}
  {% endfor %}
  
  {{ log("All datasets created successfully", info=True) }}
  
{% endmacro %}