-- models/level2_a.sql
-- Proper ref usage (good practice)
with src as (
    select *
    from {{ ref('level1_base') }}
)
select id, name, amount * 2 as amount_twice, (amount * 2) * (amount * 2) as amount_squared
from src;
