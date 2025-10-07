from datetime import datetime
from airflow import DAG
from airflow.operators.empty import EmptyOperator

with DAG("smoke_test", start_date=datetime(2024,1,1), schedule=None, catchup=False):
    EmptyOperator(task_id="ok")
