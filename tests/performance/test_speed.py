"""Performance tests for DAGLinter."""

import time
from pathlib import Path

import pytest

from daglinter.core.config import Config
from daglinter.core.engine import LintEngine
from daglinter.core.parser import ASTParser


class TestPerformance:
    """Test performance benchmarks."""

    def test_should_parse_single_file_under_100ms(self, tmp_path):
        """Single file parsing should complete under 100ms."""
        file = tmp_path / "test.py"
        file.write_text("""
from airflow import DAG
from airflow.operators.python import PythonOperator

dag = DAG('test', doc_md='Test DAG documentation')

def task():
    return "result"

task1 = PythonOperator(task_id='task1', python_callable=task, dag=dag)
""")

        parser = ASTParser()

        start = time.perf_counter()
        result = parser.parse_file(file)
        duration = (time.perf_counter() - start) * 1000  # ms

        assert result.success
        # Should parse in < 100ms (likely much faster)
        assert duration < 100.0

    def test_should_lint_100_files_under_5_seconds(self, tmp_path):
        """Linting 100 files should complete under 5 seconds."""
        # Create 100 test files
        files = []
        for i in range(100):
            file = tmp_path / f"dag_{i}.py"
            file.write_text(f"""
from airflow import DAG

dag = DAG('dag_{i}', doc_md='Documentation for DAG {i}')

def task_{i}():
    return {i}
""")
            files.append(file)

        config = Config.default()
        engine = LintEngine(config.to_dict())

        start = time.perf_counter()
        all_violations, files_scanned = engine.get_all_violations(files)
        duration = time.perf_counter() - start

        assert files_scanned == 100
        # Should complete in < 5 seconds
        assert duration < 5.0

    def test_should_benchmark_each_rule_independently(self, tmp_path):
        """Each rule should complete quickly on typical file."""
        file = tmp_path / "test.py"
        file.write_text("""
import pandas as pd
import psycopg2

conn = psycopg2.connect(host='localhost')

from airflow import DAG

dag = DAG('test')

task1 >> [task2, task3, task4, task5, task6]
""")

        from daglinter.rules.heavy_imports import HeavyImportRule
        from daglinter.rules.database_calls import DatabaseConnectionRule
        from daglinter.rules.missing_docs import MissingDocsRule
        from daglinter.rules.complex_deps import ComplexDependencyRule
        from daglinter.core.models import RuleContext
        import ast

        tree = ast.parse(file.read_text())
        context = RuleContext(
            file_path=file,
            ast_tree=tree,
            source_code=file.read_text(),
            config={}
        )

        rules = [
            HeavyImportRule(),
            DatabaseConnectionRule(),
            MissingDocsRule(),
            ComplexDependencyRule(),
        ]

        for rule in rules:
            start = time.perf_counter()
            violations = rule.analyze(context)
            duration = (time.perf_counter() - start) * 1000  # ms

            # Each rule should complete in < 50ms
            assert duration < 50.0, f"{rule.rule_id} took {duration}ms"

    def test_should_handle_large_file_efficiently(self, tmp_path):
        """Should handle large files (1000+ lines) efficiently."""
        file = tmp_path / "large.py"

        # Create a large file
        lines = ["# Comment line"] * 1000
        lines.extend([
            "from airflow import DAG",
            "dag = DAG('test', doc_md='Documentation')",
        ])

        file.write_text("\n".join(lines))

        parser = ASTParser()

        start = time.perf_counter()
        result = parser.parse_file(file)
        duration = (time.perf_counter() - start) * 1000  # ms

        assert result.success
        # Should still be reasonably fast
        assert duration < 500.0  # 500ms for 1000+ lines

    def test_should_not_cause_memory_issues(self, tmp_path):
        """Should not cause memory issues with many files."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create and lint 200 files
        files = []
        for i in range(200):
            file = tmp_path / f"dag_{i}.py"
            file.write_text(f"from airflow import DAG\ndag = DAG('dag_{i}', doc_md='Doc {i}')")
            files.append(file)

        config = Config.default()
        engine = LintEngine(config.to_dict())

        all_violations, files_scanned = engine.get_all_violations(files)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        assert files_scanned == 200
        # Memory increase should be reasonable (< 100MB)
        assert memory_increase < 100.0

    def test_should_scale_linearly_with_file_count(self, tmp_path):
        """Processing time should scale linearly with file count."""
        def create_and_lint_files(count):
            files = []
            for i in range(count):
                file = tmp_path / f"test_{count}_{i}.py"
                file.write_text(f"from airflow import DAG\ndag = DAG('dag_{i}', doc_md='Doc')")
                files.append(file)

            config = Config.default()
            engine = LintEngine(config.to_dict())

            start = time.perf_counter()
            engine.get_all_violations(files)
            return time.perf_counter() - start

        # Test with different file counts
        time_10 = create_and_lint_files(10)
        time_20 = create_and_lint_files(20)

        # 20 files should take roughly 2x as long as 10 files
        # Allow some variance (between 1.5x and 3x)
        ratio = time_20 / time_10
        assert 1.5 < ratio < 3.0

    @pytest.mark.benchmark
    def test_benchmark_full_workflow(self, tmp_path, benchmark):
        """Benchmark full workflow if pytest-benchmark is available."""
        # Create test files
        files = []
        for i in range(50):
            file = tmp_path / f"dag_{i}.py"
            file.write_text(f"""
from airflow import DAG

dag = DAG('dag_{i}', doc_md='Documentation for DAG {i}')
""")
            files.append(file)

        def run_linter():
            config = Config.default()
            engine = LintEngine(config.to_dict())
            return engine.get_all_violations(files)

        if hasattr(pytest, 'benchmark'):
            result = benchmark(run_linter)
            all_violations, files_scanned = result
            assert files_scanned == 50

    def test_should_cache_parsed_asts_efficiently(self, tmp_path):
        """Multiple rules should reuse parsed AST."""
        file = tmp_path / "test.py"
        file.write_text("from airflow import DAG\ndag = DAG('test', doc_md='Doc')")

        parser = ASTParser()

        # Parse once
        start = time.perf_counter()
        result1 = parser.parse_file(file)
        time1 = time.perf_counter() - start

        # Engine should parse once and reuse for all rules
        config = Config.default()
        engine = LintEngine(config.to_dict())

        start = time.perf_counter()
        violations = engine.lint_file(file)
        engine_time = time.perf_counter() - start

        # Engine time should not be 4x parser time (since it reuses AST)
        assert engine_time < time1 * 10  # Very generous bound

    def test_should_track_parse_time_metrics(self, tmp_path):
        """Parser should track timing metrics."""
        file = tmp_path / "test.py"
        file.write_text("from airflow import DAG")

        parser = ASTParser()
        result = parser.parse_file(file)

        assert result.parse_time_ms > 0
        assert result.parse_time_ms < 1000  # Should be well under 1 second
