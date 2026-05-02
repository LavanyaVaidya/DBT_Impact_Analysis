-- models/level3_a.sql
-- Uses proper ref to level2_a
with src as (
    select *
    from {{ ref('level2_a') }}
)
select id, name, amount_twice * 3 as amount_tripled, (amount_twice * 3) + 10 as amount_tripled_plus_10
from src;
