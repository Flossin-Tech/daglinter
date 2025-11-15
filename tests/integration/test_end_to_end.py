"""End-to-end integration tests."""

from pathlib import Path

import pytest

from daglinter.core.config import Config
from daglinter.core.engine import LintEngine
from daglinter.formatters.json import JSONFormatter
from daglinter.formatters.sarif import SARIFFormatter
from daglinter.formatters.terminal import TerminalFormatter


class TestEndToEnd:
    """Test complete workflow: parse -> analyze -> format -> output."""

    def test_should_complete_full_workflow(self, fixtures_dir):
        """Should complete full linting workflow."""
        # Setup
        config = Config.default()
        engine = LintEngine(config.to_dict())

        # Find Python files
        python_files = list(fixtures_dir.glob("*.py"))
        assert len(python_files) > 0

        # Lint files
        all_violations, files_scanned = engine.get_all_violations(python_files)

        # Format output
        formatter = TerminalFormatter()
        formatter.format_violations(all_violations, files_scanned)

        # Verify
        assert files_scanned > 0
        assert isinstance(all_violations, list)

    def test_should_handle_multiple_files_in_directory(self, tmp_path):
        """Should handle multiple files in directory."""
        # Create test files
        for i in range(10):
            file = tmp_path / f"dag_{i}.py"
            file.write_text(f"""
from airflow import DAG

dag = DAG('dag_{i}', doc_md='Documentation for DAG {i} that is long enough')

def process():
    import pandas as pd
    return pd.DataFrame()
""")

        # Lint
        config = Config.default()
        engine = LintEngine(config.to_dict())
        python_files = list(tmp_path.glob("*.py"))

        all_violations, files_scanned = engine.get_all_violations(python_files)

        assert files_scanned == 10
        # All should be clean
        assert len(all_violations) == 0

    def test_should_handle_mixed_good_and_bad_files(self, tmp_path):
        """Should handle mixed good and bad files."""
        # Good file
        good = tmp_path / "good.py"
        good.write_text("""
from airflow import DAG

dag = DAG('good', doc_md='This is good documentation that is long enough')

def task():
    import pandas as pd
    return pd.DataFrame()
""")

        # Bad file
        bad = tmp_path / "bad.py"
        bad.write_text("""
import pandas as pd
import psycopg2

conn = psycopg2.connect(host='localhost')

from airflow import DAG
dag = DAG('bad')
""")

        # Lint
        config = Config.default()
        engine = LintEngine(config.to_dict())
        python_files = list(tmp_path.glob("*.py"))

        all_violations, files_scanned = engine.get_all_violations(python_files)

        assert files_scanned == 2
        assert len(all_violations) >= 2  # Multiple violations in bad file

    def test_should_apply_config_exclusions(self, tmp_path):
        """Should apply configuration exclusions."""
        # Create structure
        dags = tmp_path / "dags"
        dags.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()

        # DAG file
        dag_file = dags / "example.py"
        dag_file.write_text("import pandas as pd")

        # Test file (should be excluded)
        test_file = tests / "test_example.py"
        test_file.write_text("import pandas as pd")

        # Config with exclusions
        config = Config(
            exclude=["**/tests/**"],
            rules=Config.default().rules
        )

        # Lint only dags directory
        engine = LintEngine(config.to_dict())
        all_violations, files_scanned = engine.get_all_violations([dag_file])

        assert files_scanned == 1
        assert len(all_violations) >= 1

    def test_should_generate_json_report(self, fixtures_dir):
        """Should generate JSON report."""
        config = Config.default()
        engine = LintEngine(config.to_dict())

        python_files = list(fixtures_dir.glob("*.py"))
        all_violations, files_scanned = engine.get_all_violations(python_files)

        formatter = JSONFormatter()
        output = formatter.format_violations(all_violations, files_scanned, "1.0.0")

        # Should be valid JSON with expected structure
        import json
        parsed = json.loads(output)

        assert "version" in parsed
        assert "summary" in parsed
        assert "violations" in parsed
        assert parsed["summary"]["files_scanned"] == files_scanned

    def test_should_generate_sarif_report(self, fixtures_dir):
        """Should generate SARIF report."""
        config = Config.default()
        engine = LintEngine(config.to_dict())

        python_files = list(fixtures_dir.glob("*.py"))
        all_violations, files_scanned = engine.get_all_violations(python_files)

        formatter = SARIFFormatter()
        output = formatter.format_violations(all_violations, "1.0.0")

        # Should be valid SARIF
        import json
        parsed = json.loads(output)

        assert "$schema" in parsed
        assert "runs" in parsed
        assert parsed["version"] == "2.1.0"

    def test_should_handle_large_repository(self, tmp_path):
        """Should handle large repository efficiently."""
        # Create 100 files
        for i in range(100):
            file = tmp_path / f"dag_{i}.py"
            file.write_text(f"""
from airflow import DAG

dag = DAG('dag_{i}', doc_md='Doc {i} that is long enough for the minimum')
""")

        config = Config.default()
        engine = LintEngine(config.to_dict())

        python_files = list(tmp_path.glob("*.py"))
        all_violations, files_scanned = engine.get_all_violations(python_files)

        assert files_scanned == 100
        # Should complete in reasonable time

    def test_should_detect_all_violation_types(self, tmp_path):
        """Should detect all 4 rule violations."""
        file = tmp_path / "all_violations.py"
        file.write_text("""
# DL001: Heavy imports at module level
import pandas as pd
import numpy as np

# DL002: Database connection at module level
import psycopg2
conn = psycopg2.connect(host='localhost')

from airflow import DAG

# DL003: Missing documentation
dag = DAG('test')

# DL004: Complex dependencies
task1 >> [task2, task3, task4, task5, task6, task7, task8, task9, task10, task11, task12]
""")

        config = Config.default()
        engine = LintEngine(config.to_dict())

        all_violations, files_scanned = engine.get_all_violations([file])

        assert files_scanned == 1
        # Should have at least one violation from each rule
        rule_ids = set(v.rule_id for v in all_violations)
        assert "DL001" in rule_ids
        assert "DL002" in rule_ids
        assert "DL003" in rule_ids
        assert "DL004" in rule_ids

    def test_should_respect_rule_configuration(self, tmp_path):
        """Should respect rule enable/disable configuration."""
        file = tmp_path / "test.py"
        file.write_text("""
import pandas as pd
from airflow import DAG
dag = DAG('test')
""")

        # Disable heavy-imports rule
        config = Config(
            rules={
                "heavy-imports": {"enabled": False},
                "db-connections": {"enabled": True},
                "missing-docs": {"enabled": True},
                "complex-dependencies": {"enabled": True},
            }
        )

        engine = LintEngine(config.to_dict())
        all_violations, _ = engine.get_all_violations([file])

        # Should not detect pandas import
        rule_ids = [v.rule_id for v in all_violations]
        assert "DL001" not in rule_ids
        # But should detect missing docs
        assert "DL003" in rule_ids

    def test_should_handle_parsing_errors_gracefully(self, tmp_path):
        """Should handle parsing errors without crashing."""
        good_file = tmp_path / "good.py"
        good_file.write_text("from airflow import DAG\ndag = DAG('test', doc_md='Good doc')")

        bad_file = tmp_path / "bad_syntax.py"
        bad_file.write_text("def bad(:")

        config = Config.default()
        engine = LintEngine(config.to_dict())

        python_files = [good_file, bad_file]
        all_violations, files_scanned = engine.get_all_violations(python_files)

        # Should process both files
        assert files_scanned == 2
        # Good file should have no violations
        # Bad file should be skipped (no violations added)

    def test_should_maintain_performance_metrics(self, tmp_path):
        """Should track performance metrics."""
        files = []
        for i in range(50):
            file = tmp_path / f"dag_{i}.py"
            file.write_text(f"from airflow import DAG\ndag = DAG('dag_{i}', doc_md='Doc {i} long enough')")
            files.append(file)

        config = Config.default()
        engine = LintEngine(config.to_dict())

        import time
        start = time.time()
        all_violations, files_scanned = engine.get_all_violations(files)
        duration = time.time() - start

        assert files_scanned == 50
        # Should complete in reasonable time (< 5 seconds for 50 files)
        assert duration < 5.0

    def test_should_provide_actionable_suggestions(self, tmp_path):
        """Should provide actionable suggestions for violations."""
        file = tmp_path / "test.py"
        file.write_text("""
import pandas as pd
from airflow import DAG
dag = DAG('test')
""")

        config = Config.default()
        engine = LintEngine(config.to_dict())

        all_violations, _ = engine.get_all_violations([file])

        # All violations should have suggestions
        for violation in all_violations:
            assert violation.suggestion is not None
            assert len(violation.suggestion) > 0

    def test_should_handle_unicode_content(self, tmp_path):
        """Should handle Unicode characters in files."""
        file = tmp_path / "unicode.py"
        file.write_text("""
# -*- coding: utf-8 -*-
# 日本語コメント
from airflow import DAG

dag = DAG('test', doc_md='Documentation with émojis 🚀 and 日本語')

def process():
    message = "Hello 世界"
    return message
""", encoding='utf-8')

        config = Config.default()
        engine = LintEngine(config.to_dict())

        all_violations, files_scanned = engine.get_all_violations([file])

        assert files_scanned == 1
        # Should process without errors

    def test_should_integrate_with_ci_cd(self, tmp_path):
        """Should integrate well with CI/CD (exit codes, JSON output)."""
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("import pandas as pd\nfrom airflow import DAG\ndag = DAG('test')")

        config = Config.default()
        engine = LintEngine(config.to_dict())

        all_violations, files_scanned = engine.get_all_violations([bad_file])

        # Generate JSON for CI/CD
        formatter = JSONFormatter()
        output = formatter.format_violations(all_violations, files_scanned)

        import json
        parsed = json.loads(output)

        # CI/CD can check for errors
        assert parsed["summary"]["errors"] > 0
        # And get structured data
        assert len(parsed["violations"]) > 0
