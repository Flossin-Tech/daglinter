# Contributing to DAGLinter

Thank you for your interest in contributing to DAGLinter! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Areas for Contribution](#areas-for-contribution)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, background, or identity.

### Expected Behavior

- Be respectful and considerate in your communication
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, trolling, or discriminatory language
- Personal attacks or insults
- Publishing others' private information
- Other conduct that could reasonably be considered inappropriate

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Familiarity with Python AST (helpful but not required)
- Basic understanding of Airflow concepts

### Setting Up Development Environment

1. **Fork and Clone**

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/daglinter.git
cd daglinter

# Add upstream remote
git remote add upstream https://github.com/Flossin-Tech/daglinter.git
```

2. **Create Virtual Environment**

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

3. **Install Dependencies**

```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

4. **Verify Installation**

```bash
# Run tests
pytest

# Run linter on itself
daglinter src/

# Check code formatting
black --check src/ tests/

# Run type checking
mypy src/
```

## Development Workflow

### 1. Create a Branch

```bash
# Fetch latest changes
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
```

**Branch Naming Convention:**
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring
- `test/description` - Test improvements

### 2. Make Changes

- Write clear, well-documented code
- Follow existing code style
- Add tests for new functionality
- Update documentation as needed

### 3. Run Tests and Checks

```bash
# Run full test suite
pytest

# Run with coverage
pytest --cov=daglinter --cov-report=html

# Check code formatting
black src/ tests/

# Run linter
ruff check src/ tests/

# Type checking
mypy src/

# Lint your own code with DAGLinter (if applicable)
daglinter src/
```

### 4. Commit Changes

Write clear commit messages following this format:

```
<type>: <short summary>

<detailed description>

<footer with issue references>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build process, tooling changes

**Example:**

```
feat: add support for custom rule plugins

Implement plugin system that allows users to define custom
linting rules. Rules can be registered via entry points and
loaded dynamically.

Closes #123
```

### 5. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create pull request on GitHub
```

## Code Standards

### Python Style Guide

We follow PEP 8 with these specifics:

- **Line Length**: 88 characters (Black default)
- **Quotes**: Double quotes for strings
- **Imports**: Sorted with `isort`
- **Formatting**: Automated with `black`

### Code Quality Tools

#### Black (Code Formatter)

```bash
# Format code
black src/ tests/

# Check without making changes
black --check src/ tests/
```

#### Ruff (Linter)

```bash
# Lint code
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/
```

#### MyPy (Type Checker)

```bash
# Check types
mypy src/

# Strict mode
mypy --strict src/daglinter/
```

### Type Hints

All public functions must have type hints:

```python
from typing import List, Optional
from pathlib import Path

def lint_file(file_path: Path, config: Optional[dict] = None) -> List[Violation]:
    """
    Lint a single Python file.

    Args:
        file_path: Path to the file to lint
        config: Optional configuration dictionary

    Returns:
        List of violations found
    """
    pass
```

### Documentation

#### Docstrings

Use Google-style docstrings:

```python
def analyze(self, context: RuleContext) -> List[Violation]:
    """
    Analyze AST and return violations.

    Args:
        context: Analysis context containing AST and metadata

    Returns:
        List of violations found in the analysis

    Raises:
        ValueError: If context is invalid

    Example:
        >>> rule = HeavyImportRule()
        >>> violations = rule.analyze(context)
    """
    pass
```

#### Comments

- Explain **why**, not **what**
- Use clear, concise language
- Update comments when code changes

```python
# Good: Explains why
# Skip validation for backward compatibility with old configs
if not config.get('strict_mode'):
    return

# Bad: States the obvious
# Set x to 5
x = 5
```

## Testing Requirements

### Test Coverage

- **Minimum Coverage**: 85% overall
- **New Code**: 100% coverage for new features
- **Critical Paths**: 100% coverage for rule logic

### Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── test_parser.py
│   ├── test_config.py
│   └── rules/
│       ├── test_heavy_imports.py
│       └── test_db_connections.py
├── integration/             # Integration tests
│   ├── test_cli.py
│   └── test_end_to_end.py
└── fixtures/                # Test fixtures
    ├── good_dag.py
    └── bad_imports.py
```

### Writing Tests

#### Unit Tests

```python
import pytest
from daglinter.rules.heavy_imports import HeavyImportRule

class TestHeavyImportRule:
    """Test heavy import detection."""

    def test_module_level_import_fails(self):
        """Module-level pandas import should fail."""
        code = """
import pandas as pd

from airflow import DAG
"""
        violations = run_rule(HeavyImportRule(), code)

        assert len(violations) == 1
        assert violations[0].rule_id == "DL001"
        assert "pandas" in violations[0].message

    def test_function_level_import_passes(self):
        """Function-level pandas import should pass."""
        code = """
from airflow import DAG

def process():
    import pandas as pd
"""
        violations = run_rule(HeavyImportRule(), code)
        assert len(violations) == 0
```

#### Integration Tests

```python
def test_cli_end_to_end(tmp_path):
    """Test full CLI workflow."""
    # Create test DAG
    dag_file = tmp_path / "test.py"
    dag_file.write_text("import pandas")

    # Run CLI
    result = subprocess.run(
        ['daglinter', str(tmp_path)],
        capture_output=True,
        text=True
    )

    # Verify
    assert result.returncode == 1
    assert "DL001" in result.stdout
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_parser.py

# Run specific test
pytest tests/unit/test_parser.py::test_parse_valid_file

# Run with coverage
pytest --cov=daglinter --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Test Fixtures

Place reusable test DAGs in `tests/fixtures/`:

```python
# tests/fixtures/good_dag.py
from airflow import DAG

dag = DAG('test', doc_md='Test DAG')

@task
def process():
    import pandas  # OK: inside task
    pass
```

## Pull Request Process

### Before Submitting

1. **Run All Checks**

```bash
# Run tests
pytest

# Check formatting
black --check src/ tests/

# Check linting
ruff check src/ tests/

# Check types
mypy src/

# Check coverage
pytest --cov=daglinter --cov-report=term-missing
```

2. **Update Documentation**

- Update README if needed
- Add/update docstrings
- Update relevant docs in `docs/`
- Add entry to CHANGELOG (if exists)

3. **Rebase on Main**

```bash
git fetch upstream
git rebase upstream/main
```

### Pull Request Template

When creating a PR, include:

**Title**: Clear, descriptive title

**Description**:
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All tests pass
- [ ] Added new tests
- [ ] Coverage maintained/improved

## Checklist
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] No breaking changes (or documented)

## Related Issues
Closes #123
```

### Review Process

1. **Automated Checks**: CI/CD runs tests, linting, type checking
2. **Code Review**: Maintainers review code for quality and correctness
3. **Discussion**: Address feedback and make changes if needed
4. **Approval**: Maintainer approves PR
5. **Merge**: Maintainer merges (squash merge preferred)

### Review Criteria

Reviewers check for:
- **Correctness**: Does it work as intended?
- **Test Coverage**: Are tests comprehensive?
- **Code Quality**: Is it readable and maintainable?
- **Documentation**: Is it well-documented?
- **Performance**: Are there performance implications?
- **Breaking Changes**: Are breaking changes necessary and documented?

## Areas for Contribution

### Good First Issues

Look for issues labeled `good-first-issue`:

- Documentation improvements
- Test coverage improvements
- Bug fixes
- Small feature additions

### High-Priority Areas

1. **Additional Linting Rules**
   - XCom anti-patterns
   - Task timeout configurations
   - Resource allocation issues
   - Security concerns

2. **Performance Improvements**
   - Parallel file processing
   - AST caching
   - Rule optimization

3. **IDE Integration**
   - VS Code extension
   - PyCharm plugin
   - Language server protocol

4. **Auto-fix Capabilities**
   - Move imports to tasks
   - Add DAG documentation
   - Suggest fixes for violations

5. **Documentation**
   - Tutorial improvements
   - More examples
   - Video guides
   - Translations

### Feature Requests

Open an issue with the `feature-request` label:

1. Describe the feature
2. Explain the use case
3. Provide examples
4. Discuss alternatives

## Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Pull Requests**: Code review and collaboration

### Questions?

- Check existing issues and discussions first
- Search documentation
- Ask in GitHub Discussions
- Tag maintainers if urgent

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- GitHub contributors page

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Thank You!

Every contribution, no matter how small, helps make DAGLinter better for everyone. Thank you for being part of the community!

---

**Happy Contributing!** 🚀
