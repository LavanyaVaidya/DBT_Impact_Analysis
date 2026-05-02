-- macros/increment_amount.sql
{% macro increment_amount(table, col, inc) %}
    select
        {{ table }}.{{ col }} + {{ inc }} as {{ col }}_incremented,
        *
    from {{ table }}
{% endmacro %}
