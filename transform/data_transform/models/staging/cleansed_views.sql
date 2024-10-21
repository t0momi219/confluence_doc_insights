with raw_views as (
    select *
    from {{ source('confluence', 'views') }}
),

raw_pages as (
    select *
    from {{ source('confluence', 'pages') }}
),

final as (
    select
        t1.page_id,
        t1.date,
        t1.views,
        t1._dlt_load_id,
        t1._dlt_id
    from
        raw_views as t1
        inner join raw_pages as t2
            on t1.page_id = t2.id
    where
        t1.date >= to_date(t2.created_at) -- 作成日よりも前の閲覧数の取得は意味がないので捨てる
)

select *
from final
