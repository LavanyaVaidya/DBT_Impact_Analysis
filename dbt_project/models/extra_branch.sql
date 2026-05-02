-- models/extra_branch.sql
-- This model joins two separate branches to create a wider DAG
with a as (
    select * from {{ ref('level3_a') }}
),
    b as (
    select * from level3_b   -- hard‑coded reference
)
select a.id, a.name, a.amount_tripled, b.amount_scaled
from a
join b on a.id = b.id;
