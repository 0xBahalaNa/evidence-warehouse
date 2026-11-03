{% set raw_s3 = source('raw', 's3_audit') %}
{% set raw_s3_rel = load_relation(raw_s3) %}
with padded as (
    {% if raw_s3_rel is none %}
    select
        null::varchar as source,
        null::varchar as check_id,
        null::varchar as resource_id,
        null::varchar as status,
        null::varchar as collected_at,
        null::varchar as enc_type,
        null::varchar as run_id,
        null::timestamptz as loaded_at
    where false
    {% else %}
    select * from {{ raw_s3 }}
    union all by name
    select
        null::varchar as enc_type
    where false
    {% endif %}
)
select
    source,
    check_id,
    resource_id,
    status,
    collected_at::timestamptz as collected_at,
    enc_type,
    run_id,
    loaded_at
from padded
