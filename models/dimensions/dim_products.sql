with stg_products as (
    select * from {{ ref('products') }}
),

product_categories as (
    select * from {{ ref('product_categories') }}
),

-- Create product dimension
dim_products as (
    select
        -- Primary key
        p.product_id,
        
        -- Foreign keys
        p.category_id,
        
        -- Product attributes
        p.name as product_name,
        p.description as product_description,
        p.price,
        
        -- Category attributes
        c.name as category_name,
        c.parent_category_id,
        
        -- Timestamps
        p.created_at,
        p.updated_at,
        
        -- Add metadata fields
        '{{ invocation_id }}' as _invocation_id,
        current_timestamp() as _loaded_at
    from stg_products p
    left join product_categories c on p.category_id = c.category_id
)

select * from dim_products