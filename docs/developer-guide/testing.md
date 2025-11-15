# Testing Guide

Comprehensive guide to testing in DAGLinter.

## Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Writing Unit Tests](#writing-unit-tests)
- [Writing Integration Tests](#writing-integration-tests)
- [Test Fixtures](#test-fixtures)
- [Coverage Requirements](#coverage-requirements)
- [Testing Best Practices](#testing-best-practices)

## Testing Philosophy

DAGLinter follows a comprehensive testing approach:

1. **Unit Tests (70%)**: Test individual components in isolation
2. **Integration Tests (25%)**: Test component interactions
3. **End-to-End Tests (5%)**: Test complete workflows

### Goals

- **Coverage**: Minimum 85% code coverage, 100% for new features
- **Reliability**: Tests must be deterministic and repeatable
- **Speed**: Full test suite should run in < 30 seconds
- **Clarity**: Tests should serve as documentation

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest configuration and fixtures
│
├── unit/                    # Unit tests
│   ├── __init__.py
│   ├── test_config.py       # Configuration tests
│   ├── test_parser.py       # AST parser tests
│   ├── test_engine.py       # Linting engine tests
│   └── rules/               # Rule tests
│       ├── test_heavy_imports.py
│       ├── test_database_calls.py
│       ├── test_missing_docs.py
│       └── test_complex_deps.py
│
├── integration/             # Integration tests
│   ├── __init__.py
│   ├── test_cli.py          # CLI integration
│   ├── test_formatters.py   # Formatter integration
│   └── test_end_to_end.py   # Complete workflows
│
├── security/                # Security tests
│   ├── __init__.py
│   └── test_malicious_input.py
│
└── fixtures/                # Test fixtures (sample DAGs)
    ├── good_dag.py
    ├── bad_imports.py
    ├── bad_db_calls.py
    ├── missing_docs.py
    ├── complex_deps.py
    └── edge_cases/
        ├── syntax_error.py
        ├── empty_file.py
        └── unicode_dag.py
```

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_parser.py

# Run specific test class
pytest tests/unit/test_parser.py::TestParser

# Run specific test method
pytest tests/unit/test_parser.py::TestParser::test_parse_valid_file

# Run tests matching pattern
pytest -k "test_heavy"
pytest -k "not slow"
```

### Coverage Reports

```bash
# Run with coverage
pytest --cov=daglinter

# Generate HTML coverage report
pytest --cov=daglinter --cov-report=html

# View report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# Show missing lines
pytest --cov=daglinter --cov-report=term-missing

# Fail if coverage below threshold
pytest --cov=daglinter --cov-fail-under=85
```

### Performance and Debugging

```bash
# Show slowest tests
pytest --durations=10

# Run in parallel (faster)
pytest -n auto

# Stop on first failure
pytest -x

# Drop into debugger on failure
pytest --pdb

# Capture print statements
pytest -s

# Show local variables on failure
pytest -l
```

## Writing Unit Tests

### Test Structure

Follow the Arrange-Act-Assert (AAA) pattern:

```python
def test_feature():
    # Arrange: Set up test data and conditions
    input_data = "test"

    # Act: Execute the code under test
    result = function_under_test(input_data)

    # Assert: Verify the results
    assert result == expected_value
```

### Testing Rules

Example unit test for a linting rule:

```python
import ast
import pytest
from pathlib import Path
from daglinter.rules.heavy_imports import HeavyImportRule
from daglinter.core.models import RuleContext, Severity

class TestHeavyImportRule:
    """Tests for heavy import detection rule."""

    def test_module_level_import_creates_violation(self):
        """Module-level pandas import should create violation."""
        # Arrange
        code = """
import pandas as pd

from airflow import DAG

dag = DAG('test')
"""
        rule = HeavyImportRule()
        context = self._create_context(code)

        # Act
        violations = rule.analyze(context)

        # Assert
        assert len(violations) == 1
        assert violations[0].rule_id == "DL001"
        assert violations[0].severity == Severity.ERROR
        assert "pandas" in violations[0].message
        assert violations[0].line == 2

    def test_function_level_import_passes(self):
        """Function-level pandas import should not create violation."""
        # Arrange
        code = """
from airflow import DAG
from airflow.decorators import task

dag = DAG('test')

@task
def process():
    import pandas as pd  # OK: inside function
    return pd.DataFrame()
"""
        rule = HeavyImportRule()
        context = self._create_context(code)

        # Act
        violations = rule.analyze(context)

        # Assert
        assert len(violations) == 0

    def test_custom_heavy_library_detected(self):
        """Custom heavy library should be detected when configured."""
        # Arrange
        code = "import custom_lib"
        rule = HeavyImportRule(config={
            'libraries': ['custom_lib']
        })
        context = self._create_context(code)

        # Act
        violations = rule.analyze(context)

        # Assert
        assert len(violations) == 1
        assert "custom_lib" in violations[0].message

    def test_disabled_rule_returns_no_violations(self):
        """Disabled rule should return no violations."""
        # Arrange
        code = "import pandas"
        rule = HeavyImportRule(config={'enabled': False})
        context = self._create_context(code)

        # Act
        violations = rule.analyze(context)

        # Assert
        assert len(violations) == 0

    # Helper method
    def _create_context(self, code: str) -> RuleContext:
        """Create a RuleContext from code string."""
        tree = ast.parse(code)
        return RuleContext(
            file_path=Path("test.py"),
            ast_tree=tree,
            source_code=code,
            source_lines=code.split('\n'),
            config={}
        )
```

### Parametrized Tests

Test multiple scenarios efficiently:

```python
import pytest

@pytest.mark.parametrize("library,expected_violation", [
    ("pandas", True),
    ("numpy", True),
    ("sklearn", True),
    ("os", False),  # Standard library
    ("airflow", False),  # Allowed library
])
def test_library_detection(library, expected_violation):
    """Test detection of various libraries."""
    code = f"import {library}"
    rule = HeavyImportRule()
    context = create_context(code)

    violations = rule.analyze(context)

    if expected_violation:
        assert len(violations) == 1
        assert library in violations[0].message
    else:
        assert len(violations) == 0
```

### Testing Edge Cases

```python
class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_file(self):
        """Empty file should not crash."""
        code = ""
        rule = HeavyImportRule()
        context = create_context(code)

        violations = rule.analyze(context)
        assert violations == []

    def test_syntax_error_handled(self):
        """Syntax errors should be handled gracefully."""
        code = "import pandas as"  # Incomplete
        # Parser should handle this, not rule
        with pytest.raises(SyntaxError):
            ast.parse(code)

    def test_unicode_content(self):
        """Unicode in code should be handled."""
        code = """
import pandas as pd
# Comment with unicode: 你好世界
"""
        rule = HeavyImportRule()
        context = create_context(code)

        violations = rule.analyze(context)
        assert len(violations) == 1
```

## Writing Integration Tests

### CLI Integration Tests

```python
import subprocess
import json
from pathlib import Path

def test_cli_basic_usage(tmp_path):
    """Test basic CLI usage."""
    # Create test DAG
    dag_file = tmp_path / "test_dag.py"
    dag_file.write_text("""
import pandas as pd
from airflow import DAG
dag = DAG('test')
""")

    # Run CLI
    result = subprocess.run(
        ['daglinter', str(tmp_path)],
        capture_output=True,
        text=True
    )

    # Assert
    assert result.returncode == 1  # Violations found
    assert "DL001" in result.stdout
    assert "pandas" in result.stdout

def test_json_output_format(tmp_path):
    """Test JSON output format."""
    # Create test DAG
    dag_file = tmp_path / "test.py"
    dag_file.write_text("import pandas")

    # Run with JSON format
    result = subprocess.run(
        ['daglinter', '--format', 'json', str(tmp_path)],
        capture_output=True,
        text=True
    )

    # Parse JSON output
    output = json.loads(result.stdout)

    # Assert structure
    assert 'summary' in output
    assert 'violations' in output
    assert output['summary']['files_scanned'] == 1
    assert len(output['violations']) >= 1
    assert output['violations'][0]['rule_id'] == 'DL001'

def test_config_file_usage(tmp_path):
    """Test using custom config file."""
    # Create config
    config_file = tmp_path / ".daglinter.yml"
    config_file.write_text("""
version: 1
rules:
  heavy-imports:
    severity: warning
""")

    # Create DAG
    dag_file = tmp_path / "test.py"
    dag_file.write_text("import pandas")

    # Run with config
    result = subprocess.run(
        ['daglinter', '--config', str(config_file), str(tmp_path)],
        capture_output=True,
        text=True
    )

    # Should show warning, not error
    assert "WARNING" in result.stdout
    assert "ERROR" not in result.stdout
```

### End-to-End Tests

```python
def test_complete_workflow(tmp_path):
    """Test complete linting workflow."""
    # Create directory structure
    dags_dir = tmp_path / "dags"
    dags_dir.mkdir()

    # Create multiple DAGs
    (dags_dir / "good_dag.py").write_text("""
from airflow import DAG
dag = DAG('good', doc_md='Good DAG')

@task
def process():
    import pandas
""")

    (dags_dir / "bad_dag.py").write_text("""
import pandas
from airflow import DAG
dag = DAG('bad')
""")

    # Create config
    config = tmp_path / ".daglinter.yml"
    config.write_text("""
version: 1
exclude:
  - "**/tests/**"
""")

    # Run linter
    result = subprocess.run(
        ['daglinter', str(dags_dir)],
        capture_output=True,
        text=True
    )

    # Verify results
    assert result.returncode == 1
    assert "good_dag.py" not in result.stdout
    assert "bad_dag.py" in result.stdout
    assert "DL001" in result.stdout
    assert "DL003" in result.stdout
```

## Test Fixtures

### Using Pytest Fixtures

Define reusable test data in `conftest.py`:

```python
# tests/conftest.py
import pytest
from pathlib import Path
import ast
from daglinter.core.models import RuleContext

@pytest.fixture
def sample_dag_code():
    """Sample valid DAG code."""
    return """
from airflow import DAG
from airflow.decorators import task

dag = DAG('test', doc_md='Test DAG')

@task
def process():
    import pandas as pd
    return pd.DataFrame()
"""

@pytest.fixture
def create_context():
    """Factory fixture to create RuleContext."""
    def _create(code: str, file_path: str = "test.py"):
        tree = ast.parse(code)
        return RuleContext(
            file_path=Path(file_path),
            ast_tree=tree,
            source_code=code,
            source_lines=code.split('\n'),
            config={}
        )
    return _create

@pytest.fixture
def temp_dag_dir(tmp_path):
    """Create temporary directory with sample DAGs."""
    dags_dir = tmp_path / "dags"
    dags_dir.mkdir()

    # Create sample DAGs
    (dags_dir / "good.py").write_text("""
from airflow import DAG
dag = DAG('good', doc_md='Good')
""")

    (dags_dir / "bad.py").write_text("""
import pandas
from airflow import DAG
dag = DAG('bad')
""")

    return dags_dir
```

### Using Fixtures in Tests

```python
def test_with_fixture(sample_dag_code, create_context):
    """Test using fixtures."""
    # Use fixture data
    context = create_context(sample_dag_code)

    # Test logic
    rule = HeavyImportRule()
    violations = rule.analyze(context)

    assert len(violations) == 0  # Sample code is good

def test_with_temp_dir(temp_dag_dir):
    """Test using temporary directory."""
    # Use temp directory
    result = subprocess.run(
        ['daglinter', str(temp_dag_dir)],
        capture_output=True
    )

    assert result.returncode == 1
```

## Coverage Requirements

### Minimum Coverage

- **Overall**: 85% line coverage
- **New Features**: 100% coverage
- **Critical Paths**: 100% coverage (rule logic, parsers)
- **Edge Cases**: Comprehensive edge case testing

### Checking Coverage

```bash
# Overall coverage
pytest --cov=daglinter --cov-report=term-missing

# Coverage for specific module
pytest --cov=daglinter.rules --cov-report=term-missing

# Fail if below threshold
pytest --cov=daglinter --cov-fail-under=85
```

### Coverage Report

```bash
# Generate HTML report
pytest --cov=daglinter --cov-report=html

# View in browser
open htmlcov/index.html
```

### What to Cover

**Must Cover:**
- All public APIs
- All rule logic
- Error handling paths
- Edge cases
- Configuration handling

**Can Skip:**
- `__repr__` methods marked with `# pragma: no cover`
- Defensive programming that can't be triggered
- Platform-specific code on other platforms

## Testing Best Practices

### 1. Test Names

Use descriptive test names:

```python
# Good
def test_module_level_pandas_import_creates_error_violation():
    pass

# Bad
def test_imports():
    pass
```

### 2. One Assertion Per Test

```python
# Good - focused test
def test_violation_has_correct_rule_id():
    violations = run_rule(code)
    assert violations[0].rule_id == "DL001"

def test_violation_has_correct_severity():
    violations = run_rule(code)
    assert violations[0].severity == Severity.ERROR

# Acceptable - related assertions
def test_violation_structure():
    violations = run_rule(code)
    assert len(violations) == 1
    assert violations[0].rule_id == "DL001"
    assert violations[0].severity == Severity.ERROR
```

### 3. Arrange-Act-Assert

Always structure tests clearly:

```python
def test_feature():
    # Arrange
    input_data = prepare_data()
    expected = calculate_expected()

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected
```

### 4. Use Fixtures for Setup

```python
# Good - use fixture
def test_with_config(config_fixture):
    result = load_config(config_fixture)
    assert result is not None

# Bad - manual setup
def test_without_fixture():
    config = {
        'rules': {
            'heavy-imports': {'enabled': True}
        }
    }
    result = load_config(config)
    assert result is not None
```

### 5. Test Both Positive and Negative

```python
def test_valid_input_succeeds():
    """Valid input should succeed."""
    result = validate("valid")
    assert result is True

def test_invalid_input_fails():
    """Invalid input should fail."""
    result = validate("invalid")
    assert result is False

def test_empty_input_raises_error():
    """Empty input should raise ValueError."""
    with pytest.raises(ValueError):
        validate("")
```

### 6. Use Markers

```python
# Mark slow tests
@pytest.mark.slow
def test_performance():
    pass

# Run only fast tests
# pytest -m "not slow"

# Mark tests by category
@pytest.mark.integration
def test_cli_integration():
    pass

# pytest -m integration
```

### 7. Mock External Dependencies

```python
from unittest.mock import patch, Mock

def test_with_mock():
    """Test with mocked external call."""
    with patch('daglinter.utils.fetch_data') as mock_fetch:
        # Configure mock
        mock_fetch.return_value = {'status': 'ok'}

        # Test
        result = process_data()

        # Verify
        assert result == expected
        mock_fetch.assert_called_once()
```

## Continuous Integration

Tests run automatically in CI/CD:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest --cov=daglinter --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## See Also

- [Development Setup](development-setup.md) - Set up development environment
- [Contributing Guide](contributing.md) - Contribution guidelines
- [Creating Rules](creating-rules.md) - How to create new rules
- [Architecture](architecture.md) - System architecture
