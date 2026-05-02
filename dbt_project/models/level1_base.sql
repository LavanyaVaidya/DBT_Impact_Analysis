-- models/level1_base.sql
with source as (
    select 1 as id, 'Alice' as name, 100 as amount
)
select *
from source;
