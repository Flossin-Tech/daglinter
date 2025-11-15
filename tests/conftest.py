"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def fixtures_dir():
    """Return path to fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def good_dag_file(fixtures_dir):
    """Return path to good DAG example."""
    return fixtures_dir / "good_dag.py"


@pytest.fixture
def bad_imports_file(fixtures_dir):
    """Return path to bad imports example."""
    return fixtures_dir / "bad_imports.py"


@pytest.fixture
def bad_db_file(fixtures_dir):
    """Return path to bad database calls example."""
    return fixtures_dir / "bad_db_calls.py"


@pytest.fixture
def missing_docs_file(fixtures_dir):
    """Return path to missing docs example."""
    return fixtures_dir / "missing_docs.py"
