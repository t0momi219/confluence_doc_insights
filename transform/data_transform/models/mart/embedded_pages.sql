with markdown as (
    select
        *
    from
        {{ ref('page_html_to_markdown') }}
),

final as (
    select
        t1.page_id,
        t2.VALUE as chunk,
        SNOWFLAKE.CORTEX.EMBED_TEXT_1024('multilingual-e5-large', t2.VALUE) as embedded_chunk,
        current_timestamp() as updated_at
    from
        markdown t1,
        lateral flatten(input => t1.chunked_contents) t2
)

select *
from final
