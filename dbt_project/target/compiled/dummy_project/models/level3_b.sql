-- models/level3_b.sql
-- Hard‑coded reference to level2_b (bad practice)
with src as (
    select *
    from level2_b   -- direct table name
)
select id, name, amount_plus_10 * 3 as amount_scaled
from src;