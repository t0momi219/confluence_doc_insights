{% set report_window = env_var('DBT__REPORT_WINDOW', 14) %}
{% set unique_views_threshold = env_var('DBT__UNIQUE_VIEWS_THRESHOLD', null) %}

with cleansed_pages as (
    -- report_window 日以内に作成されたページ
    select
        *
    from
        {{ ref('cleansed_pages') }}
    where
        age <= {{ report_window }}
),

cleansed_views as (
    -- report_window 日以内の閲覧回数
    select
        *
    from
        {{ ref('cleansed_views') }}
    where
        date <= dateadd(day, {{ report_window }}, to_date({{ get_last_load_datetime() }}))
),

cleansed_viewers as (
    -- report_window 日以内のユニーク閲覧者数
    select
        *
    from
        {{ ref('cleansed_viewers') }}
    where
        date <= dateadd(day, {{ report_window }}, to_date({{ get_last_load_datetime() }}))
),

calc_threshold as (
    -- 閾値を計算（環境変数で与えられた日付、作成されたばかりのページの日別閲覧者数の平均）
    select
        coalesce({{ unique_views_threshold }}, avg(t1.viewers)) as threshold
    from
        cleansed_viewers t1
        inner join cleansed_pages t2
            on t1.page_id = t2.page_id
),

agg_viewers as (
    -- 各ページのreport_window日以内のユニーク閲覧者数の平均
    select
        page_id,
        avg(viewers) as avg_viewers
    from
        cleansed_viewers
    group by
        page_id
),

agg_views as (
    -- 各ページのreport_window日以内の合計閲覧回数
    select
        page_id,
        sum(viewers) as total_views
    from
        cleansed_viewers
    group by
        page_id
),

final as (
    select
        to_date({{ get_last_load_datetime() }}) as agg_target_date,
        t1.space_id,
        t1.page_id,
        t1.title,
        t1.created_at,
        t1.updated_at,
        t1.path,
        t2.total_views,
        t3.avg_viewers,
        iff(
            t3.avg_viewers <= (select threshold from calc_threshold),
            '見逃されたページ',
            '活発なページ'
        ) as activity_category
    from
        cleansed_pages t1
        inner join agg_views t2
            on t1.page_id = t2.page_id
        inner join agg_viewers t3
            on t1.page_id = t3.page_id
)

select *
from final
