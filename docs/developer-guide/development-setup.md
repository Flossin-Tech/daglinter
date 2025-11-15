# Development Setup

Complete guide to setting up your DAGLinter development environment.

## Prerequisites

### Required

- **Python 3.8+**: DAGLinter supports Python 3.8 through 3.12
- **Git**: For version control
- **pip**: Python package manager (comes with Python)

### Recommended

- **Virtual environment tool**: venv, virtualenv, or conda
- **IDE**: VS Code, PyCharm, or similar with Python support
- **Terminal**: Bash, Zsh, or PowerShell

## Initial Setup

### 1. Fork and Clone Repository

```bash
# Fork the repository on GitHub
# https://github.com/Flossin-Tech/daglinter

# Clone your fork
git clone https://github.com/YOUR_USERNAME/daglinter.git
cd daglinter

# Add upstream remote
git remote add upstream https://github.com/Flossin-Tech/daglinter.git

# Verify remotes
git remote -v
```

### 2. Create Virtual Environment

#### Using venv (recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate on Linux/macOS
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate

# Verify activation
which python  # Should point to venv/bin/python
python --version  # Should be 3.8+
```

#### Using conda

```bash
# Create conda environment
conda create -n daglinter python=3.10

# Activate
conda activate daglinter

# Verify
which python
```

### 3. Install Dependencies

```bash
# Install package in editable mode with dev dependencies
pip install -e ".[dev]"

# Verify installation
daglinter --version
pytest --version
black --version
mypy --version
```

### 4. Verify Setup

```bash
# Run tests
pytest

# Should see output like:
# ======================== test session starts ========================
# collected 45 items
#
# tests/unit/test_parser.py ........                          [ 17%]
# tests/unit/test_config.py ......                            [ 31%]
# ...
# ======================== 45 passed in 2.34s ========================

# Run daglinter on itself
daglinter src/

# Should see:
# ✓ All X file(s) passed linting!
```

## Project Structure

Understanding the codebase structure:

```
daglinter/
├── src/daglinter/           # Main package
│   ├── cli/                 # Command-line interface
│   │   ├── __init__.py
│   │   └── main.py          # CLI entry point
│   ├── core/                # Core functionality
│   │   ├── config.py        # Configuration management
│   │   ├── engine.py        # Linting engine
│   │   ├── models.py        # Data models
│   │   └── parser.py        # AST parser
│   ├── rules/               # Linting rules
│   │   ├── base.py          # Base rule class
│   │   ├── heavy_imports.py # DL001
│   │   ├── database_calls.py# DL002
│   │   ├── missing_docs.py  # DL003
│   │   └── complex_deps.py  # DL004
│   ├── formatters/          # Output formatters
│   │   ├── terminal.py      # Terminal output
│   │   ├── json.py          # JSON formatter
│   │   └── sarif.py         # SARIF formatter
│   └── utils/               # Utilities
│       └── scope.py         # AST scope tracking
├── tests/                   # Test suite
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── fixtures/            # Test fixtures
├── docs/                    # Documentation
├── examples/                # Example configs
└── pyproject.toml           # Package configuration
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_parser.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=daglinter --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# Run specific test
pytest tests/unit/test_parser.py::TestParser::test_parse_valid_file

# Run tests matching pattern
pytest -k "test_heavy"
```

### Code Formatting

```bash
# Format code with Black
black src/ tests/

# Check formatting without changes
black --check src/ tests/

# Format specific file
black src/daglinter/rules/heavy_imports.py
```

### Linting

```bash
# Run Ruff linter
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/

# Check specific rules
ruff check --select F401 src/  # Check unused imports
```

### Type Checking

```bash
# Run MyPy type checker
mypy src/

# Check with strict mode
mypy --strict src/daglinter/

# Check specific file
mypy src/daglinter/core/parser.py
```

### Running DAGLinter

```bash
# Run from source (uses development version)
python -m daglinter.cli.main examples/sample_dags/

# Or use the installed command
daglinter examples/sample_dags/

# Run with different options
daglinter --verbose examples/sample_dags/
daglinter --format json examples/sample_dags/
daglinter --config .daglinter.yml examples/sample_dags/
```

## IDE Configuration

### VS Code

#### Recommended Extensions

Install these extensions:
- Python (Microsoft)
- Pylance (Microsoft)
- Black Formatter
- MyPy Type Checker
- Test Explorer UI

#### Settings

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "tests"
  ],
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.linting.mypyEnabled": true,
  "[python]": {
    "editor.rulers": [88],
    "editor.defaultFormatter": "ms-python.black-formatter"
  }
}
```

#### Launch Configuration

Create `.vscode/launch.json` for debugging:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: DAGLinter",
      "type": "python",
      "request": "launch",
      "module": "daglinter.cli.main",
      "args": ["examples/sample_dags/"],
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal"
    },
    {
      "name": "Python: Pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["-v"],
      "console": "integratedTerminal"
    }
  ]
}
```

### PyCharm

#### Configuration

1. **Interpreter**: Settings > Project > Python Interpreter
   - Select the venv interpreter

2. **Code Style**: Settings > Editor > Code Style > Python
   - Set line length to 88 (Black)
   - Enable "Reformat on Save"

3. **Testing**: Settings > Tools > Python Integrated Tools
   - Default test runner: pytest

4. **External Tools**: Settings > Tools > External Tools
   - Add Black, MyPy, Ruff as external tools

## Common Development Tasks

### Creating a New Rule

1. Create rule file in `src/daglinter/rules/`
2. Implement rule class extending `BaseRule`
3. Register rule in `src/daglinter/rules/__init__.py`
4. Add tests in `tests/unit/rules/`
5. Update documentation

Example:

```bash
# Create rule file
touch src/daglinter/rules/my_new_rule.py

# Create test file
touch tests/unit/rules/test_my_new_rule.py

# Run tests for new rule
pytest tests/unit/rules/test_my_new_rule.py
```

See [Creating Rules](creating-rules.md) for detailed guide.

### Adding a Test

```bash
# Create test file
touch tests/unit/test_new_feature.py

# Write test
cat > tests/unit/test_new_feature.py << 'EOF'
import pytest

def test_new_feature():
    """Test new feature."""
    result = my_function()
    assert result == expected
EOF

# Run test
pytest tests/unit/test_new_feature.py -v
```

### Updating Documentation

```bash
# Edit docs
vim docs/user-guide/rules.md

# Preview (if using mkdocs)
mkdocs serve

# Build docs
mkdocs build
```

### Making a Release (Maintainers)

```bash
# Update version
vim src/daglinter/__version__.py

# Update CHANGELOG
vim CHANGELOG.md

# Commit changes
git add .
git commit -m "chore: bump version to X.Y.Z"

# Tag release
git tag -a vX.Y.Z -m "Release version X.Y.Z"

# Push
git push origin main --tags

# Build package
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

## Troubleshooting

### Import Errors

```bash
# Ensure package is installed in editable mode
pip install -e ".[dev]"

# Verify installation
pip show daglinter

# Check sys.path
python -c "import sys; print('\n'.join(sys.path))"
```

### Test Failures

```bash
# Run with verbose output
pytest -vv

# Run with print statements
pytest -s

# Run single test for debugging
pytest tests/unit/test_parser.py::test_specific -vv

# Use pdb debugger
pytest --pdb
```

### Type Check Errors

```bash
# Check with detailed output
mypy --show-error-codes src/

# Ignore specific errors temporarily
mypy --ignore-errors src/

# Check single file
mypy src/daglinter/core/parser.py
```

### Performance Issues

```bash
# Profile tests
pytest --durations=10

# Profile code
python -m cProfile -o profile.stats -m daglinter.cli.main dags/
python -m pstats profile.stats

# Memory profiling
pip install memory_profiler
python -m memory_profiler src/daglinter/cli/main.py
```

## Best Practices

### Before Committing

Run this checklist:

```bash
# 1. Format code
black src/ tests/

# 2. Lint code
ruff check src/ tests/

# 3. Type check
mypy src/

# 4. Run tests
pytest

# 5. Check coverage
pytest --cov=daglinter --cov-report=term-missing

# 6. Test on examples
daglinter examples/sample_dags/
```

### Automated Pre-commit

Install pre-commit hooks:

```bash
pip install pre-commit
pre-commit install

# Now checks run automatically on commit
git commit -m "Your message"
```

## Getting Help

### Documentation

- [Contributing Guide](contributing.md)
- [Testing Guide](testing.md)
- [Creating Rules](creating-rules.md)
- [Architecture](architecture.md)

### Support

- **GitHub Issues**: Report bugs
- **GitHub Discussions**: Ask questions
- **Code Review**: Request on pull requests

## Next Steps

Now that your environment is set up:

1. **Explore the codebase**: Read existing rules and tests
2. **Pick an issue**: Look for `good-first-issue` labels
3. **Make changes**: Follow [Contributing Guide](contributing.md)
4. **Submit PR**: Create pull request for review

Happy coding! 🚀
