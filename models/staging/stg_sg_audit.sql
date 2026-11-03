{% set raw_sg = source('raw', 'sg_audit') %}
{% set raw_sg_rel = load_relation(raw_sg) %}
with padded as (
    {% if raw_sg_rel is none %}
    select
        null::varchar as source,
        null::varchar as check_id,
        null::varchar as resource_id,
        null::varchar as status,
        null::varchar as collected_at,
        null::varchar as from_port,
        null::varchar as to_port,
        null::varchar as cidr_ip,
        null::varchar as sg_name,
        null::varchar as run_id,
        null::timestamptz as loaded_at
    where false
    {% else %}
    select * from {{ raw_sg }}
    union all by name
    select
        null::varchar as from_port,
        null::varchar as to_port,
        null::varchar as cidr_ip,
        null::varchar as sg_name
    where false
    {% endif %}
)
select
    source,
    check_id,
    resource_id,
    status,
    collected_at::timestamptz as collected_at,
    from_port::varchar as from_port,
    to_port::varchar as to_port,
    cidr_ip,
    sg_name,
    run_id,
    loaded_at
from padded
