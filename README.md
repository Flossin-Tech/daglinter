# DAGLinter

[![Python Support](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type checker: mypy](https://img.shields.io/badge/type%20checker-mypy-blue.svg)](https://mypy-lang.org/)

**A static analysis tool for Apache Airflow DAG files**

DAGLinter helps you catch performance issues, anti-patterns, and maintainability problems in your Airflow DAGs before they hit production. It performs fast, offline static analysis using Python's AST parser to identify common issues that slow down DAG parsing, create resource leaks, or make DAGs hard to maintain.

## Features

- **Fast Performance Analysis** - Detects heavy library imports that slow DAG parsing (pandas, numpy, etc.)
- **Resource Leak Detection** - Identifies database connections created at module level
- **Documentation Quality** - Ensures DAGs have meaningful documentation
- **Complexity Analysis** - Warns about overly complex task dependency patterns
- **Multiple Output Formats** - Terminal (colored), JSON, and SARIF for CI/CD integration
- **Configurable Rules** - Customize severity levels, thresholds, and enable/disable rules
- **Zero Runtime Overhead** - Pure static analysis, never executes your code

## Quick Start

### Installation

```bash
pip install daglinter
```

### Basic Usage

```bash
# Lint a single DAG file
daglinter my_dag.py

# Lint all DAGs in a directory
daglinter dags/

# Output JSON for CI/CD
daglinter --format json dags/ > results.json

# Output SARIF for GitHub Code Scanning
daglinter --format sarif --output results.sarif dags/
```

## Example Output

```
Linting Results
────────────────────────────────────────────────────────────

my_dag.py
  ✗ DL001 ERROR (line 5:0)
    Heavy import 'pandas' at module level may slow DAG parsing
    → import pandas as pd
    Suggestion: Move 'import pandas' inside your task function...

  ⚠ DL003 WARNING (line 10:6)
    DAG missing meaningful documentation
    → dag = DAG('my_dag')
    Suggestion: Add doc_md parameter with DAG purpose...

────────────────────────────────────────────────────────────
Summary
  Files scanned: 1
  ✗ Errors: 1
  ⚠ Warnings: 1

✗ Linting failed with 1 error(s)
```

## Rules

DAGLinter implements four core rules:

| Rule ID | Name | Severity | Description |
|---------|------|----------|-------------|
| **DL001** | Heavy Imports | ERROR | Detects heavy libraries imported at module level |
| **DL002** | Database Connections | ERROR | Identifies database connections outside task context |
| **DL003** | Missing Documentation | WARNING | Ensures DAGs have meaningful documentation |
| **DL004** | Complex Dependencies | WARNING | Warns about excessive task fan-out/fan-in |

### DL001: Heavy Imports

**Problem**: Heavy libraries (pandas, numpy, sklearn) imported at module level slow down DAG parsing.

```python
# ❌ Bad: Module-level import
import pandas as pd

from airflow import DAG

# ✅ Good: Import inside task
from airflow import DAG
from airflow.decorators import task

@task
def process():
    import pandas as pd  # Only loaded during execution
    return pd.DataFrame()
```

### DL002: Database Connections

**Problem**: Database connections at module level create resource leaks.

```python
# ❌ Bad: Module-level connection
import psycopg2
conn = psycopg2.connect(...)

# ✅ Good: Use Airflow Hooks
from airflow.providers.postgres.hooks.postgres import PostgresHook

@task
def query():
    hook = PostgresHook(postgres_conn_id='my_db')
    return hook.get_records("SELECT * FROM table")
```

### DL003: Missing Documentation

**Problem**: Undocumented DAGs are hard to understand and maintain.

```python
# ❌ Bad: No documentation
dag = DAG('my_dag', schedule='@daily')

# ✅ Good: Clear documentation
dag = DAG(
    'my_dag',
    schedule='@daily',
    doc_md='''
    ## Purpose
    Processes daily sales data

    ## Owner
    data-team@example.com
    '''
)
```

### DL004: Complex Dependencies

**Problem**: Too many task dependencies make DAGs hard to understand.

```python
# ❌ Bad: Too many dependencies
start >> [t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11]

# ✅ Good: Use TaskGroups
from airflow.utils.task_group import TaskGroup

with TaskGroup('processing') as group:
    t1 >> t2 >> t3

start >> group
```

## Configuration

Create a `.daglinter.yml` file in your project root:

```yaml
version: 1

# Exclude patterns
exclude:
  - "**/tests/**"
  - "**/__pycache__/**"

# Rule configurations
rules:
  heavy-imports:
    enabled: true
    severity: error
    libraries:
      - pandas
      - numpy
      - sklearn

  db-connections:
    enabled: true
    severity: error

  missing-docs:
    enabled: true
    severity: warning
    min_length: 20

  complex-dependencies:
    enabled: true
    severity: warning
    max_fan_out: 10
    max_fan_in: 10
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Lint Airflow DAGs

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install daglinter
      - run: daglinter dags/

      # Upload SARIF for GitHub Code Scanning
      - run: daglinter --format sarif --output results.sarif dags/
      - uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: results.sarif
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: daglinter
        name: Lint Airflow DAGs
        entry: daglinter
        language: system
        types: [python]
        files: ^dags/
```

## Documentation

📚 **Full documentation is available in the [docs/](docs/) directory:**

### User Documentation
- [Installation Guide](docs/user-guide/installation.md)
- [Quick Start](docs/user-guide/quickstart.md)
- [Configuration Reference](docs/user-guide/configuration.md)
- [Rule Documentation](docs/user-guide/rules.md)
- [CLI Reference](docs/user-guide/cli-reference.md)
- [Usage Examples](docs/user-guide/examples.md)

### Developer Documentation
- [Contributing Guide](docs/developer-guide/contributing.md)
- [Development Setup](docs/developer-guide/development-setup.md)
- [Architecture](docs/developer-guide/architecture.md)
- [Testing Guide](docs/developer-guide/testing.md)
- [Creating Rules](docs/developer-guide/creating-rules.md)

### Project Information
- [Requirements](docs/project/requirements.md)
- [Implementation Roadmap](docs/project/roadmap.md)
- [Success Metrics](docs/project/metrics.md)

## Requirements

- Python 3.8+
- No dependency on Airflow runtime (works offline)

### Dependencies

- `rich` >= 13.0 (terminal formatting)
- `pyyaml` >= 6.0 (configuration parsing)
- `typing-extensions` >= 4.0 (Python 3.8 compatibility)

## Performance

DAGLinter is designed for speed:

- **Single file**: < 100ms (typical DAG file)
- **100 DAG files**: < 5 seconds
- **Memory usage**: < 200MB for typical projects

Performance is achieved through:
- Native Python AST parsing (no external parser)
- Single-pass analysis
- Efficient rule execution
- No code execution (static analysis only)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Areas for Contribution

- Additional linting rules
- Performance improvements
- Documentation enhancements
- Bug fixes
- Test coverage improvements

## Development

### Setup Development Environment

```bash
git clone https://github.com/Flossin-Tech/daglinter.git
cd daglinter
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
pytest --cov=daglinter --cov-report=html
```

### Code Quality

```bash
# Format code
black src/ tests/

# Type checking
mypy src/

# Linting
ruff check src/ tests/
```

## Roadmap

### MVP (v0.1.0) ✅
- [x] DL001: Heavy imports detection
- [x] DL002: Database connections detection
- [x] DL003: Missing documentation detection
- [x] DL004: Complex dependencies detection
- [x] Terminal, JSON, and SARIF output formats
- [x] Configuration file support

### Post-MVP (v0.2.0+)
- [ ] Auto-fix capabilities
- [ ] Custom rule plugin system
- [ ] IDE integration (VS Code extension)
- [ ] Performance impact estimation
- [ ] Violation suppression comments
- [ ] Additional rules based on community feedback

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/Flossin-Tech/daglinter/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Flossin-Tech/daglinter/discussions)
- **Documentation**: [docs/](docs/)

## Acknowledgments

DAGLinter was inspired by the need for better Airflow DAG quality tooling and draws inspiration from:
- pylint, flake8 (Python linting)
- hadolint (Dockerfile linting)
- The Airflow community's best practices

## Related Projects

- [Apache Airflow](https://airflow.apache.org/) - The workflow orchestration platform
- [astronomer/dag-factory](https://github.com/astronomer/dag-factory) - Generate DAGs from YAML
- [apache/airflow](https://github.com/apache/airflow) - Airflow source code

---

**Made with care by the data engineering community**
