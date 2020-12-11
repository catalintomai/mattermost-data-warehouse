{{config({
    "materialized": "incremental",
    "schema": "events",
    "tags":"hourly"
  })
}}

{% if is_incremental() %}
with rudder as (
 SELECT user_id, TO_DATE(MIN(TIMESTAMP)) AS MIN_DATE
                FROM {{ ref('mobile_events') }}
                GROUP BY 1
),

max_time as (
 SELECT MAX(timestamp) - interval '1 days' as max_time FROM {{ this }} WHERE timestamp <= CURRENT_TIMESTAMP
),

join_key as (
SELECT join_key.ID AS JOIN_KEY
          FROM {{ this }} join_key
          JOIN max_time mt
            ON join_key.timestamp >= mt.max_time
),

segment as (
SELECT segment.*
FROM {{ source('mattermost_rn_mobile_release_builds_v2', 'event') }} segment
JOIN max_time
    ON segment.timestamp >= max_time.max_time
LEFT JOIN rudder
    ON segment.user_id = rudder.user_id AND TO_DATE(segment.timestamp) >= rudder.MIN_DATE
WHERE rudder.user_id is NULL
AND segment.timestamp <= CURRENT_TIMESTAMP
AND segment.timestamp >= '2019-02-01'
AND coalesce(type, event) NOT IN ('api_profiles_get_in_channel', 'api_profiles_get_by_usernames', 'api_profiles_get_by_ids', 'application_backgrounded', 'application_opened')
)

SELECT s.*
FROM segment s
LEFT JOIN JOIN_KEY a
  ON s.id = a.JOIN_KEY
WHERE s.timestamp <= CURRENT_TIMESTAMP
AND a.join_key is null

{% else %}

with rudder as (
 SELECT user_id, TO_DATE(MIN(TIMESTAMP)) AS MIN_DATE
                FROM {{ ref('mobile_events') }}
                GROUP BY 1
)

SELECT segment.*
FROM {{ source('mattermost_rn_mobile_release_builds_v2', 'event') }} segment
LEFT JOIN rudder
    ON segment.user_id = rudder.user_id AND TO_DATE(segment.timestamp) >= rudder.MIN_DATE
WHERE rudder.user_id is NULL
AND segment.timestamp <= CURRENT_TIMESTAMP
AND segment.timestamp >= '2019-02-01'
AND coalesce(type, event) NOT IN ('api_profiles_get_in_channel', 'api_profiles_get_by_usernames', 'api_profiles_get_by_ids', 'application_backgrounded', 'application_opened')

{% endif %}