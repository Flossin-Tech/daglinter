"""File with nested imports in classes and functions."""

from airflow import DAG

dag = DAG('nested_imports_test', doc_md='Testing nested import detection')

class DataProcessor:
    """Class with imports inside methods."""

    def __init__(self):
        """Initialize processor."""
        # Import inside constructor is OK
        import json
        self.json = json

    def process_data(self):
        """Process data with pandas."""
        # Import inside method is OK for heavy libraries
        import pandas as pd
        import numpy as np

        df = pd.DataFrame()
        return df

    def connect_db(self):
        """Connect to database."""
        # DB connections inside methods are OK
        import psycopg2
        conn = psycopg2.connect(host='localhost')
        return conn

def outer_function():
    """Outer function with nested imports."""
    import tensorflow as tf  # OK - inside function

    def inner_function():
        """Inner function with imports."""
        import torch  # OK - inside nested function
        return torch.tensor([1, 2, 3])

    return inner_function()

async def async_function():
    """Async function with imports."""
    import sklearn  # OK - inside async function
    from sklearn.ensemble import RandomForestClassifier
    return RandomForestClassifier()
