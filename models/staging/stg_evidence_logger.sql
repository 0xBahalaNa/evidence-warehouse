{% set raw_evidence = source('raw', 'evidence_logger') %}
{% set raw_evidence_rel = load_relation(raw_evidence) %}
with padded as (
    {% if raw_evidence_rel is none %}
    select
        null::varchar as source,
        null::varchar as check_id,
        null::varchar as resource_id,
        null::varchar as status,
        null::varchar as collected_at,
        null::varchar as policy_file,
        null::varchar as violated_attribute,
        null::varchar as raw_message,
        null::varchar as run_id,
        null::timestamptz as loaded_at
    where false
    {% else %}
    select * from {{ raw_evidence }}
    union all by name
    select
        null::varchar as raw_message
    where false
    {% endif %}
)
select
    source,
    check_id,
    nullif(resource_id, 'None') as resource_id,
    status,
    collected_at::timestamptz as collected_at,
    policy_file,
    violated_attribute,
    raw_message,
    run_id,
    loaded_at
from padded
