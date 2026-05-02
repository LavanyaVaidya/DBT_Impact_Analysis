-- models/a.sql
with source as (
    select 1 as id, 'Alice' as name
)
select *
from source;