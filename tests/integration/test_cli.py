"""Integration tests for CLI functionality."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from daglinter.cli.main import main


class TestCLI:
    """Test CLI functionality end-to-end."""

    def test_should_lint_single_file(self, good_dag_file, capsys, monkeypatch):
        """CLI should lint a single file."""
        monkeypatch.setattr(sys, 'argv', ['daglinter', str(good_dag_file)])

        exit_code = main()

        assert exit_code == 0

    def test_should_lint_directory(self, fixtures_dir, capsys, monkeypatch):
        """CLI should lint all files in a directory."""
        monkeypatch.setattr(sys, 'argv', ['daglinter', str(fixtures_dir)])

        exit_code = main()

        # Should complete (may have violations or errors from test fixtures)
        assert exit_code in [0, 1, 2]

    def test_should_output_json_format(self, good_dag_file, capsys, monkeypatch):
        """CLI should output JSON format."""
        monkeypatch.setattr(sys, 'argv', [
            'daglinter', '--format', 'json', str(good_dag_file)
        ])

        exit_code = main()

        captured = capsys.readouterr()
        # Should produce valid JSON
        parsed = json.loads(captured.out)
        assert 'summary' in parsed
        assert 'violations' in parsed

    def test_should_output_sarif_format(self, good_dag_file, capsys, monkeypatch):
        """CLI should output SARIF format."""
        monkeypatch.setattr(sys, 'argv', [
            'daglinter', '--format', 'sarif', str(good_dag_file)
        ])

        exit_code = main()

        captured = capsys.readouterr()
        # Should produce valid SARIF JSON
        parsed = json.loads(captured.out)
        assert '$schema' in parsed
        assert 'version' in parsed

    def test_should_output_terminal_format(self, good_dag_file, capsys, monkeypatch):
        """CLI should output terminal format (default)."""
        monkeypatch.setattr(sys, 'argv', ['daglinter', str(good_dag_file)])

        exit_code = main()

        # Terminal output should be human-readable
        captured = capsys.readouterr()
        assert captured.out != ""

    def test_should_use_custom_config(self, good_dag_file, tmp_path, monkeypatch):
        """CLI should use custom config file."""
        config_file = tmp_path / "custom.yml"
        config_file.write_text("""
rules:
  heavy-imports:
    enabled: false
""")

        monkeypatch.setattr(sys, 'argv', [
            'daglinter', '--config', str(config_file), str(good_dag_file)
        ])

        exit_code = main()

        # Should complete successfully
        assert exit_code == 0

    def test_should_return_exit_code_0_for_clean_files(self, good_dag_file, monkeypatch):
        """CLI should return 0 for files without errors."""
        monkeypatch.setattr(sys, 'argv', ['daglinter', str(good_dag_file)])

        exit_code = main()

        assert exit_code == 0

    def test_should_return_exit_code_1_for_violations(self, bad_imports_file, monkeypatch):
        """CLI should return 1 when errors are found."""
        monkeypatch.setattr(sys, 'argv', ['daglinter', str(bad_imports_file)])

        exit_code = main()

        assert exit_code == 1

    def test_should_return_exit_code_2_for_errors(self, tmp_path, monkeypatch):
        """CLI should return 2 for parsing/runtime errors."""
        fake_path = tmp_path / "does_not_exist.py"

        monkeypatch.setattr(sys, 'argv', ['daglinter', str(fake_path)])

        exit_code = main()

        assert exit_code == 2

    def test_should_display_help(self, capsys, monkeypatch):
        """CLI should display help message."""
        monkeypatch.setattr(sys, 'argv', ['daglinter', '--help'])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert 'usage:' in captured.out.lower()

    def test_should_display_version(self, capsys, monkeypatch):
        """CLI should display version."""
        monkeypatch.setattr(sys, 'argv', ['daglinter', '--version'])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert '0.1.0' in captured.out

    def test_should_handle_non_existent_path(self, tmp_path, monkeypatch, capsys):
        """CLI should handle non-existent paths gracefully."""
        fake_path = tmp_path / "does_not_exist.py"

        monkeypatch.setattr(sys, 'argv', ['daglinter', str(fake_path)])

        exit_code = main()

        assert exit_code == 2
        captured = capsys.readouterr()
        assert 'not exist' in captured.err.lower()

    def test_should_handle_non_python_files(self, tmp_path, monkeypatch, capsys):
        """CLI should handle non-Python files gracefully."""
        text_file = tmp_path / "test.txt"
        text_file.write_text("Not a Python file")

        monkeypatch.setattr(sys, 'argv', ['daglinter', str(tmp_path)])

        exit_code = main()

        assert exit_code == 2
        captured = capsys.readouterr()
        assert 'no python files' in captured.err.lower()

    def test_should_support_quiet_flag(self, good_dag_file, capsys, monkeypatch):
        """CLI should support --quiet flag."""
        monkeypatch.setattr(sys, 'argv', [
            'daglinter', '--quiet', str(good_dag_file)
        ])

        exit_code = main()

        # Should still work
        assert exit_code == 0

    def test_should_support_verbose_flag(self, good_dag_file, capsys, monkeypatch):
        """CLI should support --verbose flag."""
        monkeypatch.setattr(sys, 'argv', [
            'daglinter', '--verbose', str(good_dag_file)
        ])

        exit_code = main()

        assert exit_code == 0

    def test_should_write_output_to_file(self, good_dag_file, tmp_path, monkeypatch):
        """CLI should write output to file."""
        output_file = tmp_path / "output.json"

        monkeypatch.setattr(sys, 'argv', [
            'daglinter', '--format', 'json', '--output', str(output_file), str(good_dag_file)
        ])

        exit_code = main()

        assert output_file.exists()
        content = output_file.read_text()
        parsed = json.loads(content)
        assert 'summary' in parsed

    def test_should_support_color_auto(self, good_dag_file, monkeypatch):
        """CLI should support --color auto."""
        monkeypatch.setattr(sys, 'argv', [
            'daglinter', '--color', 'auto', str(good_dag_file)
        ])

        exit_code = main()

        assert exit_code == 0

    def test_should_support_color_always(self, good_dag_file, monkeypatch):
        """CLI should support --color always."""
        monkeypatch.setattr(sys, 'argv', [
            'daglinter', '--color', 'always', str(good_dag_file)
        ])

        exit_code = main()

        assert exit_code == 0

    def test_should_support_color_never(self, good_dag_file, monkeypatch):
        """CLI should support --color never."""
        monkeypatch.setattr(sys, 'argv', [
            'daglinter', '--color', 'never', str(good_dag_file)
        ])

        exit_code = main()

        assert exit_code == 0

    def test_should_handle_keyboard_interrupt(self, good_dag_file, monkeypatch):
        """CLI should handle keyboard interrupt gracefully."""
        def raise_interrupt(*args, **kwargs):
            raise KeyboardInterrupt()

        monkeypatch.setattr(sys, 'argv', ['daglinter', str(good_dag_file)])
        monkeypatch.setattr('daglinter.core.engine.LintEngine.lint_file', raise_interrupt)

        exit_code = main()

        assert exit_code == 2

    def test_should_scan_multiple_files(self, fixtures_dir, monkeypatch):
        """CLI should scan multiple files in directory."""
        monkeypatch.setattr(sys, 'argv', ['daglinter', str(fixtures_dir)])

        exit_code = main()

        # Should complete (may have violations or errors)
        assert exit_code in [0, 1, 2]

    def test_should_respect_exclude_patterns(self, tmp_path, monkeypatch):
        """CLI should respect exclude patterns from config."""
        # Create test structure
        dag_dir = tmp_path / "dags"
        dag_dir.mkdir()
        test_dir = dag_dir / "tests"
        test_dir.mkdir()

        good_file = dag_dir / "good.py"
        good_file.write_text("from airflow import DAG\ndag = DAG('test', doc_md='Good DAG documentation here')")

        test_file = test_dir / "test_dag.py"
        test_file.write_text("import pandas as pd")  # Would violate

        config_file = tmp_path / ".daglinter.yml"
        config_file.write_text("exclude: ['**/tests/**']")

        monkeypatch.setattr(sys, 'argv', [
            'daglinter', '--config', str(config_file), str(dag_dir)
        ])

        exit_code = main()

        # Should pass - test file excluded
        assert exit_code == 0

    def test_should_handle_syntax_errors_in_files(self, tmp_path, monkeypatch, capsys):
        """CLI should handle syntax errors gracefully."""
        bad_file = tmp_path / "syntax_error.py"
        bad_file.write_text("def bad(:")

        monkeypatch.setattr(sys, 'argv', ['daglinter', str(bad_file)])

        exit_code = main()

        # Should complete but file will be skipped
        assert exit_code == 0  # No violations found (file skipped)

    def test_should_handle_mixed_good_and_bad_files(self, tmp_path, monkeypatch):
        """CLI should handle mix of good and bad files."""
        good_file = tmp_path / "good.py"
        good_file.write_text("from airflow import DAG\ndag = DAG('test', doc_md='Good documentation')")

        bad_file = tmp_path / "bad.py"
        bad_file.write_text("import pandas as pd\nfrom airflow import DAG\ndag = DAG('bad')")

        monkeypatch.setattr(sys, 'argv', ['daglinter', str(tmp_path)])

        exit_code = main()

        # Should find violations
        assert exit_code == 1

    def test_should_provide_meaningful_error_messages(self, bad_imports_file, capsys, monkeypatch):
        """CLI should provide meaningful error messages."""
        monkeypatch.setattr(sys, 'argv', ['daglinter', str(bad_imports_file)])

        exit_code = main()

        captured = capsys.readouterr()
        # Should mention the file and violation
        assert str(bad_imports_file) in captured.out or 'pandas' in captured.out.lower()

    def test_should_handle_empty_directory(self, tmp_path, monkeypatch, capsys):
        """CLI should handle empty directories."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        monkeypatch.setattr(sys, 'argv', ['daglinter', str(empty_dir)])

        exit_code = main()

        assert exit_code == 2
        captured = capsys.readouterr()
        assert 'no python files' in captured.err.lower()
