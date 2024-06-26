with source as (

    select * from {{ source('push_proxy', 'logs_eu_new') }}

),

renamed as (

    select
        type
        , time as request_at
        , elb
        , client_and_port
        , target_and_port
        , request_processing_time
        , target_processing_time
        , response_processing_time
        , elb_status_code
        , target_status_code
        , received_bytes
        , sent_bytes
        , split_part(request, ' ', 1) as http_method
        , split_part(request, ' ', 2) as url
        , split_part(request, ' ', 3) as http_version
        , user_agent
        , ssl_cipher
        , ssl_protocol
        , target_group_arn
        , trace_id
        , domain_name
        , chosen_cert_arn
        , matched_rule_priority
        , request_creation_time
        , actions_executed
        , redirect_url 
        , error_reason
        , target_port_list
        , target_status_code_list
        , classification
        , classification_reason

    from source

    where
        -- remove invalid data
        array_size(split(request, ' ')) = 3

)

select * from renamed
