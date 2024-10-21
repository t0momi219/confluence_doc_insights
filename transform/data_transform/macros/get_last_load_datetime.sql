{% macro get_last_load_datetime() %}
    (select max(inserted_at) from {{ ref('cleansed_loads') }})
{% endmacro %}
