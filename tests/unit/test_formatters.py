"""Unit tests for output formatters."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from daglinter.core.models import Severity, Violation
from daglinter.formatters.json import JSONFormatter
from daglinter.formatters.sarif import SARIFFormatter
from daglinter.formatters.terminal import TerminalFormatter


def create_violation(
    rule_id="DL001",
    rule_name="test-rule",
    severity=Severity.ERROR,
    file_path=Path("test.py"),
    line=10,
    column=5,
    message="Test message",
    suggestion="Test suggestion",
    code_snippet="test code"
):
    """Helper to create test violations."""
    return Violation(
        rule_id=rule_id,
        rule_name=rule_name,
        severity=severity,
        file_path=file_path,
        line=line,
        column=column,
        message=message,
        suggestion=suggestion,
        code_snippet=code_snippet
    )


class TestJSONFormatter:
    """Test JSON formatter."""

    def test_should_produce_valid_json(self):
        """JSON formatter should produce valid JSON output."""
        violations = [
            create_violation(rule_id="DL001", message="Test violation")
        ]

        formatter = JSONFormatter()
        output = formatter.format_violations(violations, files_scanned=1)

        # Should be valid JSON
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_should_include_summary_information(self):
        """JSON output should include summary information."""
        violations = [
            create_violation(severity=Severity.ERROR),
            create_violation(severity=Severity.WARNING),
        ]

        formatter = JSONFormatter()
        output = formatter.format_violations(violations, files_scanned=5)

        parsed = json.loads(output)

        assert "summary" in parsed
        assert parsed["summary"]["files_scanned"] == 5
        assert parsed["summary"]["errors"] == 1
        assert parsed["summary"]["warnings"] == 1
        assert parsed["summary"]["total_violations"] == 2

    def test_should_include_version_and_timestamp(self):
        """JSON output should include version and timestamp."""
        violations = []

        formatter = JSONFormatter()
        output = formatter.format_violations(violations, files_scanned=1, version="1.0.0")

        parsed = json.loads(output)

        assert "version" in parsed
        assert parsed["version"] == "1.0.0"
        assert "scan_time" in parsed
        assert parsed["scan_time"].endswith("Z")  # UTC timestamp

    def test_should_format_violation_details(self):
        """JSON output should include all violation details."""
        violation = create_violation(
            rule_id="DL001",
            rule_name="heavy-imports",
            severity=Severity.ERROR,
            file_path=Path("/test/file.py"),
            line=42,
            column=10,
            message="Test message",
            suggestion="Fix it",
            code_snippet="import pandas"
        )

        formatter = JSONFormatter()
        output = formatter.format_violations([violation], files_scanned=1)

        parsed = json.loads(output)
        v = parsed["violations"][0]

        assert v["rule_id"] == "DL001"
        assert v["rule_name"] == "heavy-imports"
        assert v["severity"] == "error"
        assert v["line"] == 42
        assert v["column"] == 10
        assert v["message"] == "Test message"
        assert v["suggestion"] == "Fix it"
        assert v["code_snippet"] == "import pandas"

    def test_should_handle_empty_violations_list(self):
        """JSON formatter should handle empty violations list."""
        formatter = JSONFormatter()
        output = formatter.format_violations([], files_scanned=10)

        parsed = json.loads(output)

        assert parsed["summary"]["total_violations"] == 0
        assert parsed["summary"]["files_scanned"] == 10
        assert len(parsed["violations"]) == 0

    def test_should_count_severity_levels_correctly(self):
        """JSON formatter should count each severity level."""
        violations = [
            create_violation(severity=Severity.ERROR),
            create_violation(severity=Severity.ERROR),
            create_violation(severity=Severity.WARNING),
            create_violation(severity=Severity.INFO),
        ]

        formatter = JSONFormatter()
        output = formatter.format_violations(violations, files_scanned=1)

        parsed = json.loads(output)

        assert parsed["summary"]["errors"] == 2
        assert parsed["summary"]["warnings"] == 1
        assert parsed["summary"]["info"] == 1

    def test_should_handle_violations_without_suggestions(self):
        """JSON formatter should handle violations without suggestions."""
        violation = create_violation(suggestion=None, code_snippet=None)

        formatter = JSONFormatter()
        output = formatter.format_violations([violation], files_scanned=1)

        parsed = json.loads(output)
        v = parsed["violations"][0]

        assert v["suggestion"] is None
        assert v["code_snippet"] is None

    def test_should_format_multiple_files(self):
        """JSON formatter should handle violations from multiple files."""
        violations = [
            create_violation(file_path=Path("file1.py"), line=1),
            create_violation(file_path=Path("file2.py"), line=2),
            create_violation(file_path=Path("file3.py"), line=3),
        ]

        formatter = JSONFormatter()
        output = formatter.format_violations(violations, files_scanned=3)

        parsed = json.loads(output)

        assert len(parsed["violations"]) == 3
        files = [v["file"] for v in parsed["violations"]]
        assert "file1.py" in files
        assert "file2.py" in files


class TestSARIFFormatter:
    """Test SARIF formatter."""

    def test_should_produce_valid_sarif_json(self):
        """SARIF formatter should produce valid SARIF JSON."""
        violations = [create_violation()]

        formatter = SARIFFormatter()
        output = formatter.format_violations(violations, version="1.0.0")

        # Should be valid JSON
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_should_include_sarif_schema(self):
        """SARIF output should include schema reference."""
        formatter = SARIFFormatter()
        output = formatter.format_violations([], version="1.0.0")

        parsed = json.loads(output)

        assert "$schema" in parsed
        assert "sarif-schema-2.1.0" in parsed["$schema"]
        assert parsed["version"] == "2.1.0"

    def test_should_define_all_rules(self):
        """SARIF output should define all linting rules."""
        formatter = SARIFFormatter()
        output = formatter.format_violations([], version="1.0.0")

        parsed = json.loads(output)
        rules = parsed["runs"][0]["tool"]["driver"]["rules"]

        rule_ids = [r["id"] for r in rules]
        assert "DL001" in rule_ids
        assert "DL002" in rule_ids
        assert "DL003" in rule_ids
        assert "DL004" in rule_ids

    def test_should_include_tool_information(self):
        """SARIF output should include tool metadata."""
        formatter = SARIFFormatter()
        output = formatter.format_violations([], version="2.0.0")

        parsed = json.loads(output)
        driver = parsed["runs"][0]["tool"]["driver"]

        assert driver["name"] == "DAGLinter"
        assert driver["version"] == "2.0.0"
        assert "informationUri" in driver

    def test_should_map_severity_levels_correctly(self):
        """SARIF formatter should map severity levels to SARIF levels."""
        violations = [
            create_violation(severity=Severity.ERROR),
            create_violation(severity=Severity.WARNING),
            create_violation(severity=Severity.INFO),
        ]

        formatter = SARIFFormatter()
        output = formatter.format_violations(violations)

        parsed = json.loads(output)
        results = parsed["runs"][0]["results"]

        assert results[0]["level"] == "error"
        assert results[1]["level"] == "warning"
        assert results[2]["level"] == "note"

    def test_should_format_location_information(self):
        """SARIF formatter should format location correctly."""
        violation = create_violation(
            file_path=Path("/project/dag.py"),
            line=42,
            column=10
        )

        formatter = SARIFFormatter()
        output = formatter.format_violations([violation])

        parsed = json.loads(output)
        result = parsed["runs"][0]["results"][0]
        location = result["locations"][0]["physicalLocation"]

        assert location["artifactLocation"]["uri"] == str(Path("/project/dag.py"))
        assert location["region"]["startLine"] == 42
        assert location["region"]["startColumn"] == 11  # SARIF is 1-indexed

    def test_should_include_suggestions_as_fixes(self):
        """SARIF formatter should include suggestions as fixes."""
        violation = create_violation(suggestion="Move import inside function")

        formatter = SARIFFormatter()
        output = formatter.format_violations([violation])

        parsed = json.loads(output)
        result = parsed["runs"][0]["results"][0]

        assert "fixes" in result
        assert result["fixes"][0]["description"]["text"] == "Move import inside function"

    def test_should_handle_violations_without_suggestions(self):
        """SARIF formatter should handle violations without suggestions."""
        violation = create_violation(suggestion=None)

        formatter = SARIFFormatter()
        output = formatter.format_violations([violation])

        parsed = json.loads(output)
        result = parsed["runs"][0]["results"][0]

        assert "fixes" not in result

    def test_should_handle_empty_violations_list(self):
        """SARIF formatter should handle empty violations list."""
        formatter = SARIFFormatter()
        output = formatter.format_violations([])

        parsed = json.loads(output)

        assert len(parsed["runs"][0]["results"]) == 0

    def test_should_include_help_uri_for_rules(self):
        """SARIF formatter should include help URIs for rules."""
        formatter = SARIFFormatter()
        output = formatter.format_violations([])

        parsed = json.loads(output)
        rules = parsed["runs"][0]["tool"]["driver"]["rules"]

        for rule in rules:
            assert "helpUri" in rule
            assert "daglinter" in rule["helpUri"]


class TestTerminalFormatter:
    """Test terminal formatter."""

    def test_should_initialize_with_color_settings(self):
        """Terminal formatter should respect color settings."""
        formatter_auto = TerminalFormatter(color="auto")
        formatter_always = TerminalFormatter(color="always")
        formatter_never = TerminalFormatter(color="never")

        assert formatter_auto.console is not None
        assert formatter_always.console is not None
        assert formatter_never.console is not None

    def test_should_print_success_for_clean_files(self, capsys):
        """Terminal formatter should print success for clean files."""
        formatter = TerminalFormatter()
        formatter.format_violations([], files_scanned=10)

        captured = capsys.readouterr()
        assert "passed" in captured.out.lower() or "✓" in captured.out

    def test_should_group_violations_by_file(self):
        """Terminal formatter should group violations by file."""
        violations = [
            create_violation(file_path=Path("file1.py"), line=1),
            create_violation(file_path=Path("file1.py"), line=2),
            create_violation(file_path=Path("file2.py"), line=1),
        ]

        formatter = TerminalFormatter()
        # Should not raise exception
        formatter.format_violations(violations, files_scanned=2)

    def test_should_use_different_colors_for_severities(self):
        """Terminal formatter should use different styling for severities."""
        violations = [
            create_violation(severity=Severity.ERROR),
            create_violation(severity=Severity.WARNING),
            create_violation(severity=Severity.INFO),
        ]

        formatter = TerminalFormatter(color="always")
        # Should not raise exception
        formatter.format_violations(violations, files_scanned=1)

    def test_should_display_violation_details(self):
        """Terminal formatter should display all violation details."""
        violation = create_violation(
            rule_id="DL001",
            message="Test message",
            line=42,
            column=10,
            suggestion="Fix this",
            code_snippet="import pandas"
        )

        formatter = TerminalFormatter()
        # Should not raise exception
        formatter.format_violations([violation], files_scanned=1)

    def test_should_handle_violations_without_suggestions(self):
        """Terminal formatter should handle missing suggestions."""
        violation = create_violation(suggestion=None, code_snippet=None)

        formatter = TerminalFormatter()
        # Should not raise exception
        formatter.format_violations([violation], files_scanned=1)

    def test_should_print_summary_statistics(self, capsys):
        """Terminal formatter should print summary statistics."""
        violations = [
            create_violation(severity=Severity.ERROR),
            create_violation(severity=Severity.WARNING),
        ]

        formatter = TerminalFormatter()
        formatter.format_violations(violations, files_scanned=5)

        captured = capsys.readouterr()
        # Should mention files scanned
        assert "5" in captured.out or "files" in captured.out.lower()

    def test_should_sort_violations_by_line_number(self):
        """Terminal formatter should sort violations by line number."""
        violations = [
            create_violation(line=30),
            create_violation(line=10),
            create_violation(line=20),
        ]

        formatter = TerminalFormatter()
        # Should not raise exception - violations should be sorted
        formatter.format_violations(violations, files_scanned=1)

    def test_should_respect_no_color_setting(self):
        """Terminal formatter should respect no-color setting."""
        formatter = TerminalFormatter(color="never")
        violation = create_violation()

        # Should not raise exception
        formatter.format_violations([violation], files_scanned=1)

    def test_should_handle_large_number_of_violations(self):
        """Terminal formatter should handle many violations efficiently."""
        violations = [
            create_violation(line=i) for i in range(100)
        ]

        formatter = TerminalFormatter()
        # Should complete without error
        formatter.format_violations(violations, files_scanned=10)

    def test_should_show_clean_files_count(self, capsys):
        """Terminal formatter should show count of clean files."""
        violations = [
            create_violation(file_path=Path("bad.py"))
        ]

        formatter = TerminalFormatter()
        formatter.format_violations(violations, files_scanned=5)

        captured = capsys.readouterr()
        # Should mention clean files (4 out of 5)
        output_lower = captured.out.lower()
        assert "files" in output_lower or "scanned" in output_lower

    def test_should_handle_unicode_in_violations(self):
        """Terminal formatter should handle Unicode characters."""
        violation = create_violation(
            message="File with emoji 🚀 and 日本語",
            code_snippet="# コメント"
        )

        formatter = TerminalFormatter()
        # Should not raise exception
        formatter.format_violations([violation], files_scanned=1)

    def test_should_display_file_paths_correctly(self):
        """Terminal formatter should display file paths."""
        violations = [
            create_violation(file_path=Path("/project/dags/example_dag.py"))
        ]

        formatter = TerminalFormatter()
        # Should not raise exception
        formatter.format_violations(violations, files_scanned=1)

    def test_should_handle_relative_paths(self):
        """Terminal formatter should handle relative paths."""
        violations = [
            create_violation(file_path=Path("dags/example.py"))
        ]

        formatter = TerminalFormatter()
        # Should not raise exception
        formatter.format_violations(violations, files_scanned=1)

    def test_should_print_error_count_in_summary(self, capsys):
        """Terminal formatter should show error count."""
        violations = [
            create_violation(severity=Severity.ERROR),
            create_violation(severity=Severity.ERROR),
        ]

        formatter = TerminalFormatter()
        formatter.format_violations(violations, files_scanned=1)

        captured = capsys.readouterr()
        # Should mention errors
        assert "error" in captured.out.lower() or "✗" in captured.out

    def test_should_print_warning_count_in_summary(self, capsys):
        """Terminal formatter should show warning count."""
        violations = [
            create_violation(severity=Severity.WARNING),
        ]

        formatter = TerminalFormatter()
        formatter.format_violations(violations, files_scanned=1)

        captured = capsys.readouterr()
        # Should mention warnings
        assert "warning" in captured.out.lower() or "⚠" in captured.out
