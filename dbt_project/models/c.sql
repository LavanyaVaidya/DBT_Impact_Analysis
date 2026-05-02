with source as (
    select 1 as user_id, 100 as amount
)
select *
from source
where user_id in (
    select id from a
);