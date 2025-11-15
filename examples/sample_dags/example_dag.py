"""Example Airflow DAG for testing DAGLinter."""

from datetime import datetime

from airflow import DAG
from airflow.decorators import task

# Good: Well-documented DAG
with DAG(
    "example_etl_pipeline",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    doc_md="""
    ## Purpose
    This DAG demonstrates a simple ETL pipeline with best practices.

    ## Schedule
    Runs daily at midnight UTC

    ## Owner
    data-engineering@example.com

    ## Description
    Extracts data from source, transforms it, and loads into warehouse.
    """,
) as dag:

    @task
    def extract_data():
        """Extract data from source system."""
        # Good: Heavy import inside task function
        import pandas as pd

        data = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
        return data.to_dict()

    @task
    def transform_data(data):
        """Transform the extracted data."""
        # Transform logic here
        return {"transformed": data}

    @task
    def load_data(data):
        """Load data into warehouse using Airflow hook."""
        from airflow.providers.postgres.hooks.postgres import PostgresHook

        # Good: Using Airflow hook for database access
        hook = PostgresHook(postgres_conn_id="warehouse")
        # Load data
        return {"status": "loaded", "records": len(data)}

    # Good: Simple, clear task dependencies
    raw_data = extract_data()
    transformed = transform_data(raw_data)
    result = load_data(transformed)
