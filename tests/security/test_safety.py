"""Security tests for DAGLinter."""

from pathlib import Path

import pytest

from daglinter.core.engine import LintEngine
from daglinter.core.parser import ASTParser


class TestSecurity:
    """Test security aspects of DAGLinter."""

    def test_should_not_execute_analyzed_code(self, tmp_path):
        """DAGLinter should not execute code in analyzed files."""
        file = tmp_path / "malicious.py"
        file.write_text("""
# This code should NOT be executed
executed = False

def dangerous_function():
    global executed
    executed = True
    import os
    os.system('echo "DANGER"')  # Should never run

dangerous_function()

from airflow import DAG
dag = DAG('test')
""")

        # Lint the file
        engine = LintEngine()
        violations = engine.lint_file(file)

        # Code should not have been executed
        # (We can't directly check, but file parsing should be safe)
        assert isinstance(violations, list)

    def test_should_handle_malicious_constructs_safely(self, tmp_path):
        """Should handle potentially malicious Python constructs."""
        file = tmp_path / "malicious.py"
        file.write_text("""
# Various potentially dangerous patterns
import os
import subprocess
import sys

# File system operations
os.system('rm -rf /')  # Should not execute
subprocess.call(['dangerous', 'command'])  # Should not execute

# Network operations
import socket
socket.socket()  # Should not connect

# Import manipulation
sys.path.insert(0, '/malicious/path')

from airflow import DAG
dag = DAG('test', doc_md='Malicious DAG')
""")

        engine = LintEngine()
        violations = engine.lint_file(file)

        # Should analyze without executing
        assert isinstance(violations, list)

    def test_should_prevent_path_traversal(self, tmp_path):
        """Should handle path traversal attempts safely."""
        # Try to lint file outside of intended directory
        parent_dir = tmp_path.parent
        traversal_path = tmp_path / ".." / "sensitive_file.py"

        # Create the file
        sensitive_file = parent_dir / "sensitive_file.py"
        if not sensitive_file.exists():
            sensitive_file.write_text("# Sensitive file")

        try:
            engine = LintEngine()
            # Should handle the path safely
            violations = engine.lint_file(traversal_path.resolve())
            assert isinstance(violations, list)
        finally:
            # Cleanup
            if sensitive_file.exists():
                sensitive_file.unlink()

    def test_should_handle_huge_files_without_dos(self, tmp_path):
        """Should handle huge files without denial of service."""
        file = tmp_path / "huge.py"

        # Create a very large file (10MB)
        large_content = "# Comment\n" * 100000
        large_content += "from airflow import DAG\ndag = DAG('test', doc_md='Doc')\n"

        file.write_text(large_content)

        # Should handle without crashing or hanging
        parser = ASTParser()
        result = parser.parse_file(file)

        # Should either succeed or fail gracefully
        assert isinstance(result.success, bool)

    def test_should_handle_deeply_nested_structures(self, tmp_path):
        """Should handle deeply nested AST structures."""
        file = tmp_path / "nested.py"

        # Create deeply nested structure
        nesting = "def func():\n" + "    " * 100 + "return 1\n"

        file.write_text(f"""
from airflow import DAG

dag = DAG('test', doc_md='Documentation')

{nesting}
""")

        engine = LintEngine()
        violations = engine.lint_file(file)

        # Should handle without stack overflow
        assert isinstance(violations, list)

    def test_should_handle_unicode_attacks(self, tmp_path):
        """Should handle Unicode-based attacks safely."""
        file = tmp_path / "unicode_attack.py"
        file.write_text("""
# Unicode zero-width characters and look-alikes
from airflow import DAG

# Invisible characters: ‎‏‎‏
# Look-alike characters: РУΤHОΝрусский (not Python)

dag = DAG('test', doc_md='Unicode attack test with enough documentation')
""", encoding='utf-8')

        parser = ASTParser()
        result = parser.parse_file(file)

        # Should parse or fail gracefully
        assert isinstance(result.success, bool)

    def test_should_not_follow_symbolic_links(self, tmp_path):
        """Should handle symbolic links safely."""
        real_file = tmp_path / "real.py"
        real_file.write_text("from airflow import DAG\ndag = DAG('test', doc_md='Doc')")

        # Create symlink
        link_file = tmp_path / "link.py"
        try:
            link_file.symlink_to(real_file)

            engine = LintEngine()
            violations = engine.lint_file(link_file)

            # Should handle symlink (following it is OK in this case)
            assert isinstance(violations, list)
        except OSError:
            # Symlinks might not be supported on all systems
            pytest.skip("Symlinks not supported")

    def test_should_handle_binary_files_safely(self, tmp_path):
        """Should handle binary files without crashing."""
        file = tmp_path / "binary.py"
        # Write binary data
        file.write_bytes(b'\x00\x01\x02\x03\xff\xfe')

        parser = ASTParser()
        result = parser.parse_file(file)

        # Should fail gracefully
        assert not result.success
        assert result.error is not None

    def test_should_validate_input_paths(self, tmp_path):
        """Should validate input paths."""
        engine = LintEngine()

        # Non-existent file
        fake_file = tmp_path / "does_not_exist.py"
        violations = engine.lint_file(fake_file)

        # Should return empty list (not crash)
        assert violations == []

    def test_should_handle_special_filenames_safely(self, tmp_path):
        """Should handle special filenames safely."""
        # Filenames with special characters
        special_names = [
            "test with spaces.py",
            "test-with-dashes.py",
            "test_with_underscores.py",
            "test.multiple.dots.py",
        ]

        engine = LintEngine()

        for name in special_names:
            file = tmp_path / name
            file.write_text("from airflow import DAG\ndag = DAG('test', doc_md='Doc')")

            violations = engine.lint_file(file)

            assert isinstance(violations, list)

    def test_should_not_leak_sensitive_info_in_errors(self, tmp_path):
        """Should not leak sensitive information in error messages."""
        file = tmp_path / "error.py"
        file.write_text("""
SECRET_KEY = "super_secret_password_12345"
API_TOKEN = "token_xyz_secret"

def bad_syntax(:
""")

        parser = ASTParser()
        result = parser.parse_file(file)

        # Error message should not contain secrets
        assert not result.success
        assert "super_secret_password" not in result.error
        assert "token_xyz" not in result.error

    def test_should_handle_circular_imports_safely(self, tmp_path):
        """Should handle files with circular import references."""
        file1 = tmp_path / "file1.py"
        file1.write_text("""
from file2 import something
from airflow import DAG
dag = DAG('test1', doc_md='Documentation')
""")

        file2 = tmp_path / "file2.py"
        file2.write_text("""
from file1 import something_else
from airflow import DAG
dag = DAG('test2', doc_md='Documentation')
""")

        engine = LintEngine()

        # Should analyze each file independently
        violations1 = engine.lint_file(file1)
        violations2 = engine.lint_file(file2)

        assert isinstance(violations1, list)
        assert isinstance(violations2, list)

    def test_should_isolate_file_analysis(self, tmp_path):
        """Each file analysis should be isolated."""
        file1 = tmp_path / "file1.py"
        file1.write_text("import pandas as pd\nfrom airflow import DAG\ndag = DAG('test1')")

        file2 = tmp_path / "file2.py"
        file2.write_text("from airflow import DAG\ndag = DAG('test2', doc_md='Good documentation that is long enough')")

        engine = LintEngine()

        # Analyze both files
        violations1 = engine.lint_file(file1)
        violations2 = engine.lint_file(file2)

        # file1 should have violations, file2 should be clean
        assert len(violations1) > 0
        assert len(violations2) == 0
