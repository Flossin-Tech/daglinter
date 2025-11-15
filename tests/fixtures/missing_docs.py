"""Example DAG without documentation."""

from datetime import datetime

from airflow import DAG
from airflow.decorators import task

# BAD: DAG without documentation
dag = DAG(
    "no_docs_dag",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
)


@task
def do_something():
    """Do something."""
    return {"result": "done"}


with dag:
    do_something()
