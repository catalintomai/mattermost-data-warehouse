{{
    config(
        {
            "materialized": "table",
            "schema": "orgm_new"
        }
    )
}}

{{ latest_record (source('orgm_raw','contact'))}}
WHERE NOT isdeleted