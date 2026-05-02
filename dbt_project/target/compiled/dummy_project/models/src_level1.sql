-- models/src_level1.sql
-- Uses source and a macro for common columns
with raw as (
    select 
    id,
    name,
    amount

    from "dummy"."raw"."raw_level1"
)
select *
from raw;