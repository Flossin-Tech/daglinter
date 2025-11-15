"""Unit tests for AST parser."""

import tempfile
from pathlib import Path

import pytest

from daglinter.core.parser import ASTParser


class TestASTParser:
    """Test AST parser functionality."""

    def test_should_parse_valid_python_file_successfully(self, tmp_path):
        """Parser should successfully parse valid Python files."""
        test_file = tmp_path / "valid.py"
        test_file.write_text("""
def hello():
    return "world"

class MyClass:
    pass
""")

        parser = ASTParser()
        result = parser.parse_file(test_file)

        assert result.success
        assert result.ast_tree is not None
        assert result.source_code is not None
        assert result.file_path == test_file
        assert result.error is None
        assert result.parse_time_ms > 0

    def test_should_handle_syntax_errors_gracefully(self, tmp_path):
        """Parser should handle syntax errors without crashing."""
        test_file = tmp_path / "syntax_error.py"
        test_file.write_text("""
def bad_syntax(:
    return "missing paren"
""")

        parser = ASTParser()
        result = parser.parse_file(test_file)

        assert not result.success
        assert result.ast_tree is None
        assert result.source_code is None
        assert result.error is not None
        assert "Syntax error" in result.error
        assert "line" in result.error.lower()

    def test_should_support_utf8_encoding(self, tmp_path):
        """Parser should handle UTF-8 encoded files correctly."""
        test_file = tmp_path / "unicode.py"
        test_file.write_text("""
# -*- coding: utf-8 -*-
# 日本語コメント
# Émojis 🚀 and special chars: café

def process():
    message = "Hello 世界"
    emoji = "🎉"
    return message
""", encoding='utf-8')

        parser = ASTParser()
        result = parser.parse_file(test_file)

        assert result.success
        assert result.ast_tree is not None
        assert "日本語" in result.source_code
        assert "🚀" in result.source_code
        assert "café" in result.source_code

    def test_should_extract_file_metadata_correctly(self, tmp_path):
        """Parser should extract correct file metadata."""
        test_file = tmp_path / "metadata_test.py"
        source = """
# Line 1
def func():  # Line 2
    pass  # Line 3
"""
        test_file.write_text(source)

        parser = ASTParser()
        result = parser.parse_file(test_file)

        assert result.success
        assert result.file_path == test_file
        assert result.source_code == source

    def test_should_have_accurate_line_numbers(self, tmp_path):
        """Parser should maintain accurate line number information."""
        test_file = tmp_path / "line_numbers.py"
        test_file.write_text("""
def first():
    pass

def second():
    return 42
""")

        parser = ASTParser()
        result = parser.parse_file(test_file)

        assert result.success
        # Check that AST has line number information
        func_nodes = [node for node in result.ast_tree.body
                     if hasattr(node, 'lineno')]
        assert len(func_nodes) > 0
        assert all(hasattr(node, 'lineno') for node in func_nodes)

    def test_should_parse_empty_file(self, tmp_path):
        """Parser should handle empty files."""
        test_file = tmp_path / "empty.py"
        test_file.write_text("")

        parser = ASTParser()
        result = parser.parse_file(test_file)

        assert result.success
        assert result.ast_tree is not None
        assert result.source_code == ""

    def test_should_parse_complex_dag_file(self, tmp_path):
        """Parser should handle complex DAG files with imports and classes."""
        test_file = tmp_path / "complex_dag.py"
        test_file.write_text("""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

default_args = {
    'owner': 'airflow',
}

with DAG(
    'example_dag',
    default_args=default_args,
    schedule='@daily',
) as dag:

    def task_func():
        import pandas as pd
        return pd.DataFrame()

    task1 = PythonOperator(
        task_id='task1',
        python_callable=task_func,
    )
""")

        parser = ASTParser()
        result = parser.parse_file(test_file)

        assert result.success
        assert result.ast_tree is not None
        assert "DAG" in result.source_code

    def test_should_handle_non_existent_file(self, tmp_path):
        """Parser should handle non-existent files."""
        test_file = tmp_path / "does_not_exist.py"

        parser = ASTParser()
        result = parser.parse_file(test_file)

        assert not result.success
        assert result.error is not None

    def test_should_handle_file_with_invalid_encoding(self, tmp_path):
        """Parser should handle files with encoding issues."""
        test_file = tmp_path / "bad_encoding.py"
        # Write binary data that's not valid UTF-8
        test_file.write_bytes(b'\xff\xfe\x00\x00')

        parser = ASTParser()
        result = parser.parse_file(test_file)

        assert not result.success
        assert result.error is not None
        assert "error" in result.error.lower()

    def test_should_parse_string_successfully(self):
        """Parser should parse Python string into AST."""
        code = """
def hello():
    return "world"
"""

        parser = ASTParser()
        result = parser.parse_string(code)

        assert result.success
        assert result.ast_tree is not None
        assert result.source_code == code
        assert result.error is None

    def test_should_parse_string_with_custom_filename(self):
        """Parser should use custom filename for string parsing."""
        code = "x = 1"
        filename = "custom_name.py"

        parser = ASTParser()
        result = parser.parse_string(code, filename)

        assert result.success
        assert result.file_path.name == filename

    def test_should_handle_string_with_syntax_error(self):
        """Parser should handle syntax errors in string parsing."""
        code = "def bad(:"

        parser = ASTParser()
        result = parser.parse_string(code)

        assert not result.success
        assert result.ast_tree is None
        assert result.error is not None
        assert "Syntax error" in result.error

    def test_should_track_parse_time(self, tmp_path):
        """Parser should track parsing time."""
        test_file = tmp_path / "timing.py"
        test_file.write_text("x = 1")

        parser = ASTParser()
        result = parser.parse_file(test_file)

        assert result.parse_time_ms >= 0

    def test_should_parse_file_with_multiline_strings(self, tmp_path):
        """Parser should handle multiline strings correctly."""
        test_file = tmp_path / "multiline.py"
        test_file.write_text('''
doc_string = """
This is a
multiline string
with multiple lines
"""

def func():
    """Docstring here."""
    pass
''')

        parser = ASTParser()
        result = parser.parse_file(test_file)

        assert result.success
        assert "multiline string" in result.source_code

    def test_should_parse_file_with_nested_structures(self, tmp_path):
        """Parser should handle deeply nested structures."""
        test_file = tmp_path / "nested.py"
        test_file.write_text("""
class Outer:
    class Inner:
        def method(self):
            def nested_func():
                return lambda x: x + 1
            return nested_func
""")

        parser = ASTParser()
        result = parser.parse_file(test_file)

        assert result.success
        assert result.ast_tree is not None

    def test_should_handle_file_with_decorators(self, tmp_path):
        """Parser should handle decorators correctly."""
        test_file = tmp_path / "decorators.py"
        test_file.write_text("""
from airflow.decorators import task, dag

@dag
def my_dag():
    pass

@task
def my_task():
    pass
""")

        parser = ASTParser()
        result = parser.parse_file(test_file)

        assert result.success
        assert "@task" in result.source_code
        assert "@dag" in result.source_code

    def test_should_handle_async_functions(self, tmp_path):
        """Parser should handle async/await syntax."""
        test_file = tmp_path / "async_code.py"
        test_file.write_text("""
async def fetch_data():
    await something()
    return data
""")

        parser = ASTParser()
        result = parser.parse_file(test_file)

        assert result.success
        assert "async" in result.source_code
