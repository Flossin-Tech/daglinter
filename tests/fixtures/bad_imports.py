"""Example DAG with heavy imports at module level."""

from datetime import datetime

# BAD: Heavy imports at module level
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier

from airflow import DAG
from airflow.decorators import task

dag = DAG(
    "bad_imports_dag",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
)


@task
def process():
    """Process data using pandas."""
    df = pd.DataFrame({"a": [1, 2, 3]})
    arr = np.array([1, 2, 3])
    model = RandomForestClassifier()
    return {"result": "done"}


with dag:
    process()
