import streamlit as st

DATABASE = "PLEASE_SET_YOUR_DATABASE_NAME"
SCHEMA = "PLEASE_SET_YOUR_SCHEMA_NAME"

# すべてのスペースを取得
ALL_SPACES = f"""
    select
        space_id,
        name
    from
        {DATABASE}.{SCHEMA}.cleansed_spaces
"""

# 最終クエリ日付
LAST_RUN_DATE_QUERY = f"""
    select
        max(agg_target_date) as date
    from
        {DATABASE}.{SCHEMA}.recent_page_activity
"""

# 最近作成されたページの件数取得
# 直近2日分を取得する。
RECENT_PAGE_ACTIVITY_QUERY = f"""
    select
        agg_target_date,
        count(page_id) as added_pages,
        sum(
            iff(activity_category='活発なページ', 1, 0)
        ) as hot_pages,
        sum(
            iff(activity_category='見逃されたページ', 1, 0)
        ) as unreaded_pages,
    from
        {DATABASE}.{SCHEMA}.recent_page_activity
    where
        -- 直近２日分（２番目に大きい日付以上）
        agg_target_date >= (
            select
                distinct agg_target_date
            from
                {DATABASE}.{SCHEMA}.recent_page_activity
            order by
                agg_target_date desc
            limit 1 offset 1
        )
        and space_id = ?
    group by
        agg_target_date
    order by
        agg_target_date
"""

# 最近作成されたページの詳細情報取得
RECENT_PAGE_ACTIVITY_DETAILS_QUERY = f"""
    select
        agg_target_date,
        space_id,
        page_id,
        title,
        created_at,
        updated_at,
        path,
        total_views,
        avg_viewers,
        activity_category
    from
        {DATABASE}.{SCHEMA}.recent_page_activity
    where
        agg_target_date = (
            select
                max(agg_target_date)
            from
                {DATABASE}.{SCHEMA}.recent_page_activity
        )
        and space_id = ?
"""

# 古くなったページの件数取得
# 直近2日分を取得する。
OUTDATED_PAGE_ACTIVITY_QUERY = f"""
    select
        agg_target_date,
        count(page_id) as total_pages,
        sum(
            iff(activity_category='活発なページ', 1, 0)
        ) as hot_pages,
        sum(
            iff(activity_category='見逃されたページ', 1, 0)
        ) as unreaded_pages,
        sum(
            iff(activity_category='安定したページ', 1, 0)
        ) as stable_pages,
        sum(
            iff(activity_category='アーカイブ', 1, 0)
        ) as archive_pages,
    from
        {DATABASE}.{SCHEMA}.outdated_page_activity
    where
        -- 直近２日分（２番目に大きい日付以上）
        agg_target_date >= (
            select
                distinct agg_target_date
            from
                {DATABASE}.{SCHEMA}.outdated_page_activity
            order by
                agg_target_date desc
            limit 1 offset 1
        )
        and space_id = ?
    group by
        agg_target_date
    order by
        agg_target_date
"""

# 古くなったページの詳細情報取得
OUTDATED_PAGE_ACTIVITY_DETAILS_QUERY = f"""
    select
        agg_target_date,
        space_id,
        page_id,
        title,
        created_at,
        updated_at,
        path,
        total_views,
        avg_viewers,
        activity_category
    from
        {DATABASE}.{SCHEMA}.outdated_page_activity
    where
        agg_target_date = (
            select
                max(agg_target_date)
            from
                {DATABASE}.{SCHEMA}.outdated_page_activity
        )
        and space_id = ?
        and activity_category = ?
"""

# ページのユニークアクセス数を取得
PAGES_UNIQUE_USER_ACCESS_HISTORY_QUERY = f"""
    select
        t2.title,
        t1.date,
        t1.viewers
    from
        {DATABASE}.{SCHEMA}.cleansed_viewers t1
        inner join {DATABASE}.{SCHEMA}.cleansed_pages t2
            on t1.page_id = t2.page_id
    where
        space_id = ?
        and contains((select parse_json(?)), t1.page_id)
"""

# ページの本文（マークダウン）を取得
PAGE_MD_CONTENTS_QUERY = f"""
    select
        md_contents
    from
        {DATABASE}.{SCHEMA}.page_html_to_markdown
    where
        page_id = ?
"""

# 質問文に答えるRAGクエリ
SEARCH_ASSISTANT_QUERY = f"""
    with similar_pages as (
        select
            page_id,
            vector_cosine_similarity(embedded_chunk,
                SNOWFLAKE.CORTEX.EMBED_TEXT_1024('multilingual-e5-large', ?)
            ) as similarity
        from
            {DATABASE}.{SCHEMA}.EMBEDDED_PAGES
        order by
            similarity desc
        limit 1
    ),

    target_page as (
        select
            t1.page_id,
            md_contents,
            similarity
        from
            {DATABASE}.{SCHEMA}.PAGE_HTML_TO_MARKDOWN t1
            inner join similar_pages t2
                on t1.page_id = t2.page_id
    ),

    generate_response as (
        select
            snowflake.cortex.complete('llama3.1-70b', 
                '与えられたコンテキストの情報を用いて、質問に回答してください。
    コンテキストに回答のための情報が含まれていなかった場合には、そう言ってください。
    ## 質問
    ' || ? || '
    ## コンテキスト
    ' || md_contents),
        page_id,
        md_contents,
        similarity
        from
            target_page
        order by 
            similarity
    )

    select * from generate_response
"""

REVIEW_QUERY = f"""
    select
        snowflake.cortex.complete('reka-flash',?)
    from
        {DATABASE}.{SCHEMA}.page_html_to_markdown
"""
