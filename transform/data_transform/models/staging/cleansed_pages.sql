with raw_pages as (
    select
        *
    from
        {{ source('confluence', 'pages') }}
    where
        status in ('current')
),

loads as (
    select
        *
    from
        {{ source('confluence', '_dlt_loads') }}
),

cleansed as (
    select
        id as page_id,
        status,
        title,
        space_id,
        parent_id,
        parent_type,
        position,
        author_id,
        owner_id,
        version__author_id as last_author_id,
        version__number as version,
        created_at,
        version__created_at as updated_at,
        body__storage__value as html_contents,
        sys_connect_by_path(title, ' / ') as path,
        _dlt_load_id,
        _dlt_id
    from
        raw_pages
        start with parent_id is null
        connect by
            parent_id = prior page_id
        order by
            page_id
),

final as (
    select
        cleansed.*,
        loads.inserted_at,
        datediff(day, cleansed.created_at,loads.inserted_at) as age,
        datediff(day, greatest(cleansed.created_at, cleansed.updated_at), loads.inserted_at) as days_since_last_updated
    from
        cleansed
        inner join loads
            on cleansed._dlt_load_id = loads.load_id
)

select *
from final
