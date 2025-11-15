"""Example of a well-written DAG file."""

from datetime import datetime

from airflow import DAG
from airflow.decorators import task

# Good: DAG with documentation
dag = DAG(
    "good_example_dag",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    doc_md="""
    ## Purpose
    This DAG demonstrates best practices for Airflow DAG development.

    ## Schedule
    Runs daily at midnight UTC

    ## Owner
    data-engineering-team@example.com
    """,
)


@task
def process_data():
    """Process data with heavy library imported inside task."""
    # Good: Heavy import inside task function
    import pandas as pd

    data = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    return data.to_dict()


@task
def save_results(data):
    """Save results using Airflow hook."""
    # Good: Using Airflow hook for database access
    from airflow.providers.postgres.hooks.postgres import PostgresHook

    hook = PostgresHook(postgres_conn_id="my_postgres")
    # Save data using hook
    return {"status": "saved"}


# Good: Simple task dependencies
with dag:
    data = process_data()
    result = save_results(data)
