with raw_spaces as (
    select
        *
    from
        {{ source('confluence', 'spaces') }}
),

loads as (
    select
        *
    from
        {{ source('confluence', '_dlt_loads') }}
),

cleansed as (
    select
        id as space_id,
        created_at,
        author_id,
        homepage_id,
        name,
        key,
        type,
        status,
        _links__webui,
        _dlt_load_id,
        _dlt_id
    from
        raw_spaces
),

final as (
    select
        cleansed.*,
        loads.inserted_at
    from
        cleansed
        inner join loads
            on cleansed._dlt_load_id = loads.load_id
)

select *
from final
