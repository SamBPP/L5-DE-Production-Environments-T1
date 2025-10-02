from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator, ShortCircuitOperator

# Import your pipeline entrypoint
# Ensure PYTHONPATH includes the workspace root (set in devcontainer.json)
from pipeline.runner import process_all_to_master

# Configure data locations
BASE_PATH = "/workspaces/L5-DE-Production-Environments-T1"
IN_DIR = f"{BASE_PATH}/input/ingestion"
PROCESSED_DIR = f"{BASE_PATH}/input/processed"
OUT_DIR = f"{BASE_PATH}/output"
PATTERN = "*.csv.gz"
MASTER_NAME = "master.csv.gz"

default_args = {
    "owner": "data_eng",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="hmda_pipeline",
    start_date=datetime(2025, 10, 1),
    schedule="*/5 * * * *",   # every 5 minutes
    catchup=False,
    max_active_runs=1,        # avoid overlapping runs
    default_args=default_args,
    description="Process new inbound files into master and move to processed/",
) as dag:

    def _new_files_exist() -> bool:
        in_files = {p.name for p in Path(IN_DIR).glob(PATTERN)}
        proc_files = {p.name for p in Path(PROCESSED_DIR).glob(PATTERN)}
        new_found = len(in_files - proc_files) > 0
        if not new_found:
            print("No new files to process.")
        else:
            print(f"New files: {sorted(in_files - proc_files)}")
        return new_found

    check_new = ShortCircuitOperator(
        task_id="check_new_files",
        python_callable=_new_files_exist,
    )

    def _run_pipeline():
        in_dir = Path(IN_DIR)
        processed_dir = Path(PROCESSED_DIR)
        out_dir = Path(OUT_DIR)
        out_dir.mkdir(parents=True, exist_ok=True)
        master_path = out_dir / MASTER_NAME

        # Fresh master only if it doesn't exist yet
        fresh_master = not master_path.exists()

        result = process_all_to_master(
            in_dir=in_dir,
            processed_dir=processed_dir,
            pattern=PATTERN,
            master_path=master_path,
            fresh_master=fresh_master,
        )
        print(f"Pipeline complete. Master at: {result}")
        return str(result)

    process = PythonOperator(
        task_id="process_pipeline",
        python_callable=_run_pipeline,
    )

    check_new >> process
