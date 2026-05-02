-- models/src_level1.sql
-- Uses source and a macro for common columns
with raw as (
    select {{ common_columns() }}
    from {{ source('raw', 'raw_level1') }}
)
select *
from raw;
