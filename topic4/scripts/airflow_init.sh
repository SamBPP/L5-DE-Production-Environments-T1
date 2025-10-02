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