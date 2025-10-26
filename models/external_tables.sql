-- This file creates external tables in BigQuery using the dbt-external-tables package
-- Run this file with: dbt run-operation stage_external_sources

{{ config(
    materialized = 'ephemeral'
) }}

-- This is a placeholder model that doesn't do anything
-- The actual external table creation happens when you run the stage_external_sources operation
select 1 as placeholder