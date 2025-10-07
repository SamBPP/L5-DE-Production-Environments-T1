# Using Airflow
Below you’ll see instructions for a Codespaces devcontainer that pre-installs Airflow, a DAG that calls your `process_all_to_master(...)`, and the exact run steps (for Codespaces).

---

# 1) Minimal Codespaces setup for Airflow

Create a devcontainer so Codespaces boots a Python 3.11 workspace with Airflow preinstalled and the right env vars for imports and ports.

## `.devcontainer/devcontainer.json`

```json
{
  "name": "Airflow Codespace",
  "image": "mcr.microsoft.com/devcontainers/python:3.11",
  "features": {
    "ghcr.io/devcontainers/features/common-utils:2": {}
  },
  "containerEnv": {
    "AIRFLOW_HOME": "${containerWorkspaceFolder}/.airflow",
    "AIRFLOW__CORE__LOAD_EXAMPLES": "False",
    "PYTHONPATH": "${containerWorkspaceFolder}"
  },
  "forwardPorts": [8080],
  "postCreateCommand": "pip install --upgrade pip && pip install -r requirements.txt && bash scripts/airflow_init.sh",
  "customizations": {
    "vscode": {
      "extensions": ["ms-python.python", "ms-python.vscode-pylance", "qwtel.sqlite-viewer"]
    }
  }
}
```

## `.devcontainer/Dockerfile` (optional — only if you want OS deps)

```dockerfile
# Not strictly required for sqlite + LocalExecutor, kept here for extensibility.
FROM mcr.microsoft.com/devcontainers/python:3.11
```

---

# 2) Dependencies and bootstrap

Pin Airflow using its constraints file (the safe way to install). Keep your existing libs too.

## `requirements.txt`

```txt
pandas>=2.0
# your other deps...
# Airflow pin + constraints (match Python version: 3.11 here)
apache-airflow==2.9.3
```

> If you prefer strict constraints:
> `pip install "apache-airflow==2.9.3" --constraint https://raw.githubusercontent.com/apache/airflow/constraints-2.9.3/constraints-3.11.txt`

## `scripts/airflow_init.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

# Ensure folders exist
mkdir -p "$AIRFLOW_HOME"/{dags,logs,plugins}

# Initialise sqlite metadata DB if it doesn't exist
if [ ! -f "$AIRFLOW_HOME/airflow.db" ]; then
  airflow db init
fi

echo "Airflow initialised. To run inside Codespaces:"
echo "1) Start in one terminal:  airflow webserver -p 8080"
echo "2) Start in another:       airflow scheduler"
echo "Or simply run:             airflow standalone"
```

Make it executable:

```bash
chmod +x scripts/airflow_init.sh
```

---

# 3) Your DAG that calls the pipeline

This DAG runs every 5 minutes. It first checks for any **new** files (present in `in_dir` but not in `processed_dir`). If none, it short-circuits and the run ends quickly. If found, it calls your `process_all_to_master(...)`, which appends to the master and moves processed files—exactly your desired behaviour.

## `dags/pipeline_dag.py`

```python
from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator, ShortCircuitOperator

# Import your pipeline entrypoint
# Ensure PYTHONPATH includes the workspace root (set in devcontainer.json)
from pipeline.runner import process_all_to_master

# Configure data locations via env vars (override in Codespaces if you like)
IN_DIR = os.getenv("PIPELINE_IN_DIR", "data/in")
PROCESSED_DIR = os.getenv("PIPELINE_PROCESSED_DIR", "data/processed")
OUT_DIR = os.getenv("PIPELINE_OUT_DIR", "data/out")
PATTERN = os.getenv("PIPELINE_PATTERN", "*.csv.gz")
MASTER_NAME = os.getenv("PIPELINE_MASTER_NAME", "master.csv.gz")

default_args = {
    "owner": "data_eng",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="hmda_pipeline",
    start_date=datetime(2024, 1, 1),
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
```

This uses **sqlite** and the **LocalExecutor** by default (great for a single-container Codespace). It’s efficient and easy to maintain.

---

# 4) Run it in Codespaces

1. Open the repo in Codespaces. The devcontainer will build, install deps, and bootstrap Airflow.
2. In the terminal, start Airflow. Either:

   * One-liners:

     ```bash
     airflow standalone
     ```

     This starts both webserver and scheduler and auto-creates an admin user; or
   * Separate processes:

     ```bash
     airflow webserver -p 8080
     airflow scheduler
     ```
3. Codespaces will auto-forward **port 8080**. Open the forwarded URL to access the Airflow UI.
4. Drop a few test files into `data/in/` (you can upload via the VS Code explorer). Within 5 minutes, the DAG run will detect them, run your pipeline, append to `data/out/master.csv.gz`, and move inputs to `data/processed/`.

If you want it to react faster, change `schedule="*/2 * * * *"` or even `"* * * * *"`.

---


Happy Airflow-ing!
