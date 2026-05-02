-- models/level4_a.sql
-- Proper ref chain continuing from level3_a
with src as (
    select *
    from "dummy"."main"."level3_a"
)
select id, name, amount_tripled + 5 as amount_plus_5, (amount_trippled + 5) / 2 as amount_half_plus_5
from src;