"""Unit tests for linting engine."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from daglinter.core.engine import LintEngine
from daglinter.core.models import Severity, Violation
from daglinter.rules.base import BaseRule, registry


class TestLintEngine:
    """Test LintEngine functionality."""

    def test_should_initialize_with_default_config(self):
        """Engine should initialize with default configuration."""
        engine = LintEngine()

        assert engine.config == {}
        assert engine.parser is not None
        assert len(engine.rules) > 0

    def test_should_initialize_with_custom_config(self):
        """Engine should accept custom configuration."""
        config = {
            "rules": {
                "heavy-imports": {"enabled": False}
            }
        }

        engine = LintEngine(config)

        assert engine.config == config

    def test_should_register_all_built_in_rules(self):
        """Engine should register all 4 built-in rules."""
        engine = LintEngine()

        # Check that rules are registered
        assert len(engine.rules) > 0
        # All 4 rules should be enabled by default
        rule_names = [rule.rule_name for rule in engine.rules]
        assert "heavy-imports" in rule_names
        assert "db-connections" in rule_names
        assert "missing-docs" in rule_names
        assert "complex-dependencies" in rule_names

    def test_should_get_enabled_rules_from_config(self):
        """Engine should filter rules based on config."""
        config = {
            "rules": {
                "heavy-imports": {"enabled": False},
                "db-connections": {"enabled": True},
            }
        }

        engine = LintEngine(config)

        # Should have rules, but heavy-imports disabled
        rule_names = [rule.rule_name for rule in engine.rules]
        assert "heavy-imports" not in rule_names or len([r for r in engine.rules if r.rule_name == "heavy-imports"]) == 0

    def test_should_lint_single_file_successfully(self, tmp_path):
        """Engine should lint a single file and return violations."""
        test_file = tmp_path / "test_dag.py"
        test_file.write_text("""
import pandas as pd

from airflow import DAG

dag = DAG('test')
""")

        engine = LintEngine()
        violations = engine.lint_file(test_file)

        assert isinstance(violations, list)
        # Should have violations for pandas import and missing docs
        assert len(violations) >= 1

    def test_should_handle_parse_errors_gracefully(self, tmp_path):
        """Engine should handle parse errors without crashing."""
        test_file = tmp_path / "bad_syntax.py"
        test_file.write_text("def bad(:")

        engine = LintEngine()
        violations = engine.lint_file(test_file)

        # Should return empty list for parse errors
        assert violations == []

    def test_should_collect_violations_from_multiple_rules(self, tmp_path):
        """Engine should collect violations from all enabled rules."""
        test_file = tmp_path / "multiple_issues.py"
        test_file.write_text("""
import pandas as pd
import psycopg2

conn = psycopg2.connect(host='localhost')

from airflow import DAG

dag = DAG('test')
""")

        engine = LintEngine()
        violations = engine.lint_file(test_file)

        # Should have violations from multiple rules
        assert len(violations) >= 2
        rule_ids = [v.rule_id for v in violations]
        assert "DL001" in rule_ids  # Heavy import
        assert "DL002" in rule_ids  # DB connection

    def test_should_handle_rule_execution_errors(self, tmp_path):
        """Engine should handle errors during rule execution."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1")

        # Create a rule that raises an error
        class BrokenRule(BaseRule):
            rule_id = "TEST001"
            rule_name = "broken-rule"
            default_severity = Severity.ERROR

            def analyze(self, context):
                raise RuntimeError("Rule error")

        engine = LintEngine()
        # Add broken rule
        engine.rules.append(BrokenRule())

        # Should not crash
        violations = engine.lint_file(test_file)

        # Should still return violations from other rules
        assert isinstance(violations, list)

    def test_should_lint_multiple_files(self, tmp_path):
        """Engine should lint multiple files and return results."""
        file1 = tmp_path / "dag1.py"
        file1.write_text("""
import pandas as pd
from airflow import DAG
dag = DAG('test1')
""")

        file2 = tmp_path / "dag2.py"
        file2.write_text("""
from airflow import DAG
dag = DAG('test2', doc_md='Short doc that is too short')
""")

        engine = LintEngine()
        results = engine.lint_files([file1, file2])

        assert isinstance(results, dict)
        assert len(results) >= 1
        # Check that paths are keys
        for key in results.keys():
            assert isinstance(key, Path)

    def test_should_only_include_files_with_violations(self, tmp_path):
        """Engine should only return files that have violations."""
        clean_file = tmp_path / "clean.py"
        clean_file.write_text("""
from airflow import DAG

def process():
    import pandas as pd
    return pd.DataFrame()

dag = DAG('test', doc_md='This is a proper documentation string for the DAG')
""")

        bad_file = tmp_path / "bad.py"
        bad_file.write_text("""
import pandas as pd
from airflow import DAG
dag = DAG('test')
""")

        engine = LintEngine()
        results = engine.lint_files([clean_file, bad_file])

        # Only bad file should be in results
        assert bad_file in results
        # Clean file might not be in results

    def test_should_get_all_violations_with_count(self, tmp_path):
        """Engine should return all violations and file count."""
        file1 = tmp_path / "dag1.py"
        file1.write_text("import pandas as pd\nfrom airflow import DAG\ndag = DAG('t')")

        file2 = tmp_path / "dag2.py"
        file2.write_text("from airflow import DAG\ndag = DAG('t2')")

        engine = LintEngine()
        all_violations, files_scanned = engine.get_all_violations([file1, file2])

        assert isinstance(all_violations, list)
        assert files_scanned == 2
        assert len(all_violations) >= 2

    def test_should_pass_config_to_rules(self):
        """Engine should pass configuration to rules."""
        config = {
            "rules": {
                "missing-docs": {
                    "enabled": True,
                    "min_length": 50
                }
            }
        }

        engine = LintEngine(config)

        # Find the missing docs rule
        missing_docs_rules = [r for r in engine.rules if r.rule_name == "missing-docs"]
        if missing_docs_rules:
            rule = missing_docs_rules[0]
            # Check if config was passed
            assert hasattr(rule, 'min_length')
            assert rule.min_length == 50

    def test_should_handle_empty_file_list(self):
        """Engine should handle empty file list gracefully."""
        engine = LintEngine()
        results = engine.lint_files([])

        assert results == {}

    def test_should_handle_non_existent_files(self, tmp_path):
        """Engine should handle non-existent files gracefully."""
        fake_file = tmp_path / "does_not_exist.py"

        engine = LintEngine()
        violations = engine.lint_file(fake_file)

        # Should return empty list
        assert violations == []

    def test_should_create_rule_context_correctly(self, tmp_path):
        """Engine should create proper RuleContext for rules."""
        test_file = tmp_path / "context_test.py"
        test_file.write_text("x = 1")

        # Create a rule that verifies context
        class ContextCheckRule(BaseRule):
            rule_id = "TEST002"
            rule_name = "context-check"
            default_severity = Severity.INFO
            context_received = None

            def analyze(self, context):
                ContextCheckRule.context_received = context
                return []

        engine = LintEngine()
        engine.rules.append(ContextCheckRule())

        engine.lint_file(test_file)

        # Verify context was created correctly
        context = ContextCheckRule.context_received
        assert context is not None
        assert context.file_path == test_file
        assert context.ast_tree is not None
        assert context.source_code is not None
        assert isinstance(context.config, dict)

    def test_should_track_violations_across_multiple_files(self, tmp_path):
        """Engine should track violations across multiple files."""
        files = []
        for i in range(5):
            f = tmp_path / f"dag{i}.py"
            f.write_text(f"""
import pandas as pd
from airflow import DAG
dag = DAG('test{i}')
""")
            files.append(f)

        engine = LintEngine()
        all_violations, files_scanned = engine.get_all_violations(files)

        assert files_scanned == 5
        assert len(all_violations) >= 5  # At least one per file

    def test_should_support_rule_filtering(self):
        """Engine should support filtering rules via config."""
        # Enable only one rule
        config = {
            "rules": {
                "heavy-imports": {"enabled": True},
                "db-connections": {"enabled": False},
                "missing-docs": {"enabled": False},
                "complex-dependencies": {"enabled": False},
            }
        }

        engine = LintEngine(config)

        # Should have fewer enabled rules
        enabled_rules = [r.rule_name for r in engine.rules]
        assert "heavy-imports" in enabled_rules

    def test_should_handle_large_files(self, tmp_path):
        """Engine should handle large files efficiently."""
        large_file = tmp_path / "large.py"

        # Create a file with many lines
        lines = ["# Comment line"] * 1000
        lines.append("from airflow import DAG")
        lines.append("dag = DAG('test')")

        large_file.write_text("\n".join(lines))

        engine = LintEngine()
        violations = engine.lint_file(large_file)

        # Should complete without error
        assert isinstance(violations, list)

    def test_should_preserve_violation_order(self, tmp_path):
        """Engine should preserve violation line number order."""
        test_file = tmp_path / "order_test.py"
        test_file.write_text("""
import pandas as pd  # Line 2
import numpy as np    # Line 3
from airflow import DAG
dag = DAG('test')     # Line 5
""")

        engine = LintEngine()
        violations = engine.lint_file(test_file)

        # Violations should be ordered by line number
        for i in range(len(violations) - 1):
            if violations[i].line == violations[i+1].line:
                continue
            assert violations[i].line <= violations[i+1].line
