-- models/level5_a.sql
-- Proper ref extending to depth 5
with src as (
    select *
    from {{ ref('level4_a') }}
)
select id, name, amount_plus_5 * 2 as final_amount, (amount_plus_5 * 2) + 1 as final_amount_plus_1
from src;
