-- models/level2_b.sql
-- Hard‑coded reference (bad practice, bypasses dbt's DAG)
with src as (
    select *
    from level1_base   -- direct table name, no <dbt.context.providers.RuntimeRefResolver object at 0x00000278D2E199A0>
)
select id, name, amount + 10 as amount_plus_10
from src;