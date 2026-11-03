{% set raw_cloudtrail = source('raw', 'cloudtrail_audit') %}
{% set raw_cloudtrail_rel = load_relation(raw_cloudtrail) %}
with padded as (
    {% if raw_cloudtrail_rel is none %}
    select
        null::varchar as source,
        null::varchar as check_id,
        null::varchar as resource_id,
        null::varchar as status,
        null::varchar as collected_at,
        null::varchar as event_time,
        null::varchar as event_name,
        null::varchar as event_source,
        null::varchar as principal,
        null::varchar as error_code,
        null::varchar as source_ip,
        null::varchar as native_severity,
        null::varchar as run_id,
        null::timestamptz as loaded_at
    where false
    {% else %}
    select * from {{ raw_cloudtrail }}
    union all by name
    select
        null::varchar as event_source,
        null::varchar as principal,
        null::varchar as error_code,
        null::varchar as source_ip
    where false
    {% endif %}
)
select
    source,
    check_id,
    resource_id,
    case status
        when 'CRITICAL' then 'FAIL'
        when 'WARN' then 'WARN'
        when 'INFO' then 'WARN'
        else error(
            'stg_cloudtrail_audit: unmapped status: '
            || coalesce(status, '<NULL>')
        )
    end as status,
    collected_at::timestamptz as collected_at,
    event_time::timestamptz as event_time,
    event_name,
    event_source,
    nullif(principal, 'N/A') as principal,
    error_code,
    nullif(source_ip, 'N/A') as source_ip,
    native_severity,
    run_id,
    loaded_at
from padded
