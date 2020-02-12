{{config({
    "materialized": "table",
    "schema": "staging"
  })
}}

WITH max_timestamp              AS (
    SELECT
        server.timestamp::DATE AS date
      , server.user_id
      , max(server.timestamp)  AS max_timestamp
    FROM {{ source('mattermost2', 'server') }}
    GROUP BY 1, 2
),
     mattermost2_server_staging AS (
         SELECT
             s.timestamp::DATE AS date
           , s.user_id         AS server_id
           , s.version
           , s.context_library_version
           , s.edition
           , s.system_admins
           , s.operating_system
           , s.database_type
           , s.event
           , s.event_text
           , s.sent_at
           , s.received_at
           , s.timestamp
           , s.original_timestamp
         FROM {{ source('mattermost2', 'server') }} s
              JOIN max_timestamp mt
                   ON s.user_id = mt.user_id
                       AND s.timestamp = mt.max_timestamp
         GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14
     )
SELECT *
FROM mattermost2_server_staging;