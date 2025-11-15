"""Example DAG with database connections at module level."""

from datetime import datetime

import psycopg2

from airflow import DAG
from airflow.decorators import task

# BAD: Database connection at module level
conn = psycopg2.connect(
    host="localhost", database="mydb", user="user", password="pass"
)

dag = DAG(
    "bad_db_dag",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
)


@task
def query_database():
    """Query database using module-level connection."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()


with dag:
    query_database()
