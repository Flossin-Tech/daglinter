"""Unit tests for linting rules."""

import ast
from pathlib import Path

import pytest

from daglinter.core.models import RuleContext, Severity
from daglinter.rules.complex_deps import ComplexDependencyRule
from daglinter.rules.database_calls import DatabaseConnectionRule
from daglinter.rules.heavy_imports import HeavyImportRule
from daglinter.rules.missing_docs import MissingDocsRule


def create_context(code: str, config=None) -> RuleContext:
    """Helper to create RuleContext from code string."""
    tree = ast.parse(code)
    return RuleContext(
        file_path=Path("test.py"), ast_tree=tree, source_code=code, config=config or {}
    )


class TestHeavyImportRule:
    """Test heavy import detection."""

    def test_module_level_import_detected(self):
        """Module-level pandas import should be detected."""
        code = """
import pandas as pd

from airflow import DAG
"""
        rule = HeavyImportRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1
        assert violations[0].rule_id == "DL001"
        assert "pandas" in violations[0].message

    def test_function_level_import_allowed(self):
        """Function-level pandas import should pass."""
        code = """
from airflow.decorators import task

@task
def process():
    import pandas as pd
    return pd.DataFrame()
"""
        rule = HeavyImportRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 0

    def test_from_import_detected(self):
        """From imports should also be detected."""
        code = """
from numpy import array
"""
        rule = HeavyImportRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1
        assert "numpy" in violations[0].message

    def test_should_detect_tensorflow_import(self):
        """Should detect TensorFlow imports."""
        code = "import tensorflow as tf"
        rule = HeavyImportRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1
        assert "tensorflow" in violations[0].message

    def test_should_detect_scipy_import(self):
        """Should detect SciPy imports."""
        code = "from scipy import stats"
        rule = HeavyImportRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1
        assert "scipy" in violations[0].message

    def test_should_detect_sklearn_import(self):
        """Should detect scikit-learn imports."""
        code = "from sklearn.ensemble import RandomForestClassifier"
        rule = HeavyImportRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1
        assert "sklearn" in violations[0].message

    def test_should_detect_aliased_imports(self):
        """Should detect imports with aliases."""
        code = """
import pandas as pd
import numpy as np
"""
        rule = HeavyImportRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 2

    def test_should_allow_imports_inside_task_decorator(self):
        """Imports inside @task decorated functions should be allowed."""
        code = """
from airflow.decorators import task

@task
def my_task():
    import pandas as pd
    import numpy as np
    return pd.DataFrame()
"""
        rule = HeavyImportRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 0

    def test_should_allow_imports_in_class_methods(self):
        """Imports inside class methods should be allowed."""
        code = """
class MyOperator:
    def execute(self):
        import pandas as pd
        return pd.DataFrame()
"""
        rule = HeavyImportRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 0

    def test_should_detect_submodule_imports(self):
        """Should detect imports from heavy library submodules."""
        code = "from pandas.core.frame import DataFrame"
        rule = HeavyImportRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1

    def test_should_support_custom_heavy_libraries(self):
        """Should support custom list of heavy libraries."""
        code = "import custom_heavy_lib"
        config = {"libraries": ["custom_heavy_lib"]}
        rule = HeavyImportRule(config)
        context = create_context(code, config)
        violations = rule.analyze(context)

        assert len(violations) == 1
        assert "custom_heavy_lib" in violations[0].message

    def test_should_handle_async_functions(self):
        """Should allow imports in async functions."""
        code = """
async def async_task():
    import pandas as pd
    return pd.DataFrame()
"""
        rule = HeavyImportRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 0

    def test_should_have_error_severity(self):
        """Heavy import rule should have ERROR severity."""
        rule = HeavyImportRule()
        assert rule.default_severity == Severity.ERROR

    def test_should_include_helpful_suggestion(self):
        """Violations should include helpful suggestions."""
        code = "import pandas as pd"
        rule = HeavyImportRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1
        assert violations[0].suggestion is not None
        assert "inside your task function" in violations[0].suggestion


class TestDatabaseConnectionRule:
    """Test database connection detection."""

    def test_psycopg2_connection_detected(self):
        """Module-level psycopg2.connect should be detected."""
        code = """
import psycopg2

conn = psycopg2.connect(host='localhost')
"""
        rule = DatabaseConnectionRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1
        assert violations[0].rule_id == "DL002"
        assert "connect" in violations[0].message.lower()

    def test_function_level_connection_allowed(self):
        """Function-level connection should pass."""
        code = """
import psycopg2

def query_db():
    conn = psycopg2.connect(host='localhost')
    return conn
"""
        rule = DatabaseConnectionRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 0

    def test_should_detect_create_engine(self):
        """Should detect SQLAlchemy create_engine."""
        code = """
from sqlalchemy import create_engine

engine = create_engine('postgresql://localhost/db')
"""
        rule = DatabaseConnectionRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1
        assert "create_engine" in violations[0].message

    def test_should_detect_mongo_client(self):
        """Should detect MongoDB MongoClient."""
        code = """
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
"""
        rule = DatabaseConnectionRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1

    def test_should_allow_airflow_hooks(self):
        """Airflow hooks should be allowed."""
        code = """
from airflow.hooks.postgres_hook import PostgresHook

hook = PostgresHook(postgres_conn_id='my_conn')
"""
        rule = DatabaseConnectionRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 0

    def test_should_detect_sqlite3_connect(self):
        """Should detect sqlite3.connect."""
        code = """
import sqlite3

conn = sqlite3.connect('database.db')
"""
        rule = DatabaseConnectionRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1

    def test_should_detect_mysql_connector(self):
        """Should detect MySQL connector."""
        code = """
import mysql.connector

conn = mysql.connector.connect(host='localhost')
"""
        rule = DatabaseConnectionRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1

    def test_should_detect_redis_connection(self):
        """Should detect Redis connection."""
        code = """
import redis

r = redis.Redis(host='localhost', port=6379)
"""
        rule = DatabaseConnectionRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1

    def test_should_allow_connections_in_async_functions(self):
        """Connections in async functions should be allowed."""
        code = """
import psycopg2

async def query():
    conn = psycopg2.connect(host='localhost')
    return conn
"""
        rule = DatabaseConnectionRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 0

    def test_should_allow_connections_in_class_methods(self):
        """Connections in class methods should be allowed."""
        code = """
import psycopg2

class DatabaseHandler:
    def connect(self):
        return psycopg2.connect(host='localhost')
"""
        rule = DatabaseConnectionRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 0

    def test_should_have_error_severity(self):
        """Database connection rule should have ERROR severity."""
        rule = DatabaseConnectionRule()
        assert rule.default_severity == Severity.ERROR

    def test_should_include_helpful_suggestion(self):
        """Violations should include helpful suggestions."""
        code = """
import psycopg2
conn = psycopg2.connect(host='localhost')
"""
        rule = DatabaseConnectionRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1
        assert violations[0].suggestion is not None
        assert "Hook" in violations[0].suggestion


class TestMissingDocsRule:
    """Test DAG documentation detection."""

    def test_dag_without_docs_detected(self):
        """DAG without documentation should be detected."""
        code = """
from airflow import DAG

dag = DAG('test_dag', schedule='@daily')
"""
        rule = MissingDocsRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1
        assert violations[0].rule_id == "DL003"

    def test_dag_with_docs_passes(self):
        """DAG with sufficient documentation should pass."""
        code = """
from airflow import DAG

dag = DAG(
    'test_dag',
    schedule='@daily',
    doc_md='This is a comprehensive documentation for the DAG explaining its purpose'
)
"""
        rule = MissingDocsRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 0

    def test_dag_with_short_docs_detected(self):
        """DAG with too short documentation should be detected."""
        code = """
from airflow import DAG

dag = DAG('test_dag', doc_md='Test')
"""
        rule = MissingDocsRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1

    def test_should_detect_dag_with_empty_doc(self):
        """DAG with empty documentation should be detected."""
        code = """
from airflow import DAG

dag = DAG('test', doc_md='')
"""
        rule = MissingDocsRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1

    def test_should_support_description_parameter(self):
        """Should support 'description' parameter."""
        code = """
from airflow import DAG

dag = DAG('test', description='This is a comprehensive description of the DAG')
"""
        rule = MissingDocsRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 0

    def test_should_support_doc_parameter(self):
        """Should support 'doc' parameter."""
        code = """
from airflow import DAG

dag = DAG('test', doc='This is a comprehensive doc string for the DAG')
"""
        rule = MissingDocsRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 0

    def test_should_detect_multiple_dags_in_file(self):
        """Should detect missing docs in multiple DAGs."""
        code = """
from airflow import DAG

dag1 = DAG('dag1')
dag2 = DAG('dag2', doc_md='Sufficient documentation for dag2')
dag3 = DAG('dag3')
"""
        rule = MissingDocsRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 2  # dag1 and dag3

    def test_should_reject_placeholder_docs(self):
        """Should reject placeholder documentation."""
        code = """
from airflow import DAG

dag = DAG('test', doc_md='TODO')
"""
        rule = MissingDocsRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1

    def test_should_support_custom_min_length(self):
        """Should support custom minimum documentation length."""
        code = """
from airflow import DAG

dag = DAG('test', doc_md='Short doc')
"""
        config = {"min_length": 5}
        rule = MissingDocsRule(config)
        context = create_context(code, config)
        violations = rule.analyze(context)

        # Should pass with min_length=5
        assert len(violations) == 0

    def test_should_handle_dag_context_manager(self):
        """Should detect DAGs created with context manager."""
        code = """
from airflow import DAG

with DAG('test') as dag:
    pass
"""
        rule = MissingDocsRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1

    def test_should_have_warning_severity(self):
        """Missing docs rule should have WARNING severity."""
        rule = MissingDocsRule()
        assert rule.default_severity == Severity.WARNING

    def test_should_include_helpful_suggestion(self):
        """Violations should include helpful suggestions."""
        code = """
from airflow import DAG
dag = DAG('test')
"""
        rule = MissingDocsRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1
        assert violations[0].suggestion is not None
        assert "doc_md" in violations[0].suggestion


class TestComplexDependencyRule:
    """Test complex dependency detection."""

    def test_excessive_fan_out_detected(self):
        """Task with too many downstream dependencies should be detected."""
        code = """
task1 >> [task2, task3, task4, task5, task6, task7, task8, task9, task10, task11, task12]
"""
        rule = ComplexDependencyRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1
        assert violations[0].rule_id == "DL004"
        assert "downstream" in violations[0].message.lower()

    def test_simple_dependencies_pass(self):
        """Simple task dependencies should pass."""
        code = """
task1 >> task2 >> task3
"""
        rule = ComplexDependencyRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 0

    def test_should_detect_excessive_fan_in(self):
        """Task with too many upstream dependencies should be detected."""
        code = """
[task1, task2, task3, task4, task5, task6, task7, task8, task9, task10, task11, task12] >> final_task
"""
        rule = ComplexDependencyRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1
        assert "upstream" in violations[0].message.lower()

    def test_should_handle_upstream_operator(self):
        """Should detect dependencies using << operator."""
        code = """
task12 << [task1, task2, task3, task4, task5, task6, task7, task8, task9, task10, task11]
"""
        rule = ComplexDependencyRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1

    def test_should_support_custom_thresholds(self):
        """Should support custom fan-out/fan-in thresholds."""
        code = """
task1 >> [task2, task3, task4, task5, task6]
"""
        config = {"max_fan_out": 3}
        rule = ComplexDependencyRule(config)
        context = create_context(code, config)
        violations = rule.analyze(context)

        assert len(violations) == 1

    def test_should_handle_chained_dependencies(self):
        """Should handle chained task dependencies."""
        code = """
task1 >> task2 >> task3 >> task4 >> task5
"""
        rule = ComplexDependencyRule()
        context = create_context(code)
        violations = rule.analyze(context)

        # Should not violate - linear chain
        assert len(violations) == 0

    def test_should_handle_tuple_dependencies(self):
        """Should handle tuple syntax for dependencies."""
        code = """
task1 >> (task2, task3, task4, task5, task6, task7, task8, task9, task10, task11, task12)
"""
        rule = ComplexDependencyRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1

    def test_should_have_warning_severity(self):
        """Complex dependency rule should have WARNING severity."""
        rule = ComplexDependencyRule()
        assert rule.default_severity == Severity.WARNING

    def test_should_include_helpful_suggestion(self):
        """Violations should include helpful suggestions."""
        code = """
task1 >> [task2, task3, task4, task5, task6, task7, task8, task9, task10, task11, task12]
"""
        rule = ComplexDependencyRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 1
        assert violations[0].suggestion is not None
        assert "TaskGroup" in violations[0].suggestion

    def test_should_handle_no_dependencies(self):
        """Should handle code with no dependencies."""
        code = """
from airflow import DAG
dag = DAG('test')
"""
        rule = ComplexDependencyRule()
        context = create_context(code)
        violations = rule.analyze(context)

        assert len(violations) == 0

    def test_should_track_multiple_tasks(self):
        """Should track dependencies for multiple tasks."""
        code = """
task1 >> [task2, task3, task4]
task5 >> [task6, task7, task8]
"""
        rule = ComplexDependencyRule()
        context = create_context(code)
        violations = rule.analyze(context)

        # Should pass - no single task exceeds threshold
        assert len(violations) == 0
