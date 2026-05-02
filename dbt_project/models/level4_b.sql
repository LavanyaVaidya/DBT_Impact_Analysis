-- models/level4_b.sql
-- Hard‑coded reference to level3_b
with src as (
    select *
    from level3_b   -- bypasses dbt ref
)
select id, name, amount_scaled - 2 as amount_minus_2
from src;
