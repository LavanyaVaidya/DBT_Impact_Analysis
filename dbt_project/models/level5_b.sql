-- models/level5_b.sql
-- Hard‑coded reference to level4_b (depth 5 but bad practice)
with src as (
    select *
    from level4_b   -- direct table name
)
select id, name, amount_minus_2 / 2 as final_amount_half
from src;
