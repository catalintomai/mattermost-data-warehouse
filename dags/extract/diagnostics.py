import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from dags.airflow_utils import DATA_IMAGE, clone_and_setup_extraction_cmd, pod_defaults, mm_failed_task
from dags.kube_secrets import (
    DIAGNOSTIC_LOCATION_ONE,
    DIAGNOSTIC_LOCATION_TWO,
    SNOWFLAKE_LOAD_USER,
    SNOWFLAKE_LOAD_PASSWORD,
    SNOWFLAKE_ACCOUNT,
    SNOWFLAKE_LOAD_DATABASE,
    SNOWFLAKE_LOAD_WAREHOUSE,
)

# Load the env vars into a dict and set Secrets
env = os.environ.copy()

# Default arguments for the DAG
default_args = {
    "catchup": False,
    "depends_on_past": False,
    "on_failure_callback": mm_failed_task,
    "owner": "airflow",
    "retries": 0,
    "retry_delay": timedelta(minutes=1),
    "start_date": datetime(2019, 1, 1),
}

# Set the command for the container
# Note the {{{{ }}}} is because we format this string but want the resulting string to just have {{ yesterday_ds }}
container_cmd = f"""
    {clone_and_setup_extraction_cmd} &&
    python extract/s3_extract/diagnostics_job.py {{{{ yesterday_ds }}}}
"""

# Create the DAG
dag = DAG(
    "diagnostics", default_args=default_args, schedule_interval="0 5 * * *"
)

KubernetesPodOperator(
    **pod_defaults,
    image=DATA_IMAGE,
    task_id="diagnostics",
    name="diagnostics",
    secrets=[
        DIAGNOSTIC_LOCATION_ONE,
        DIAGNOSTIC_LOCATION_TWO,
        SNOWFLAKE_LOAD_USER,
        SNOWFLAKE_LOAD_PASSWORD,
        SNOWFLAKE_ACCOUNT,
        SNOWFLAKE_LOAD_DATABASE,
        SNOWFLAKE_LOAD_WAREHOUSE,
    ],
    env_vars={},
    arguments=[container_cmd],
    dag=dag,
)
