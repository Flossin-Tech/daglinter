# Quick Start Guide

Get started with DAGLinter in 5 minutes!

## Installation

```bash
# Install from PyPI (when published)
pip install daglinter

# Or install from source
git clone https://github.com/Flossin-Tech/daglinter.git
cd daglinter
pip install -e .
```

## Your First Lint

### Lint a Single File

```bash
daglinter my_dag.py
```

### Lint a Directory

```bash
daglinter dags/
```

## Understanding the Output

When DAGLinter finds issues, you'll see colorful, helpful output:

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

## Common Issues and Quick Fixes

### Issue 1: Heavy Import at Module Level (DL001)

**Problem**: Heavy libraries like pandas, numpy imported at module level slow DAG parsing.

**Bad**:
```python
import pandas as pd  # ❌ Slows DAG parsing

from airflow import DAG

dag = DAG('example')
```

**Good**:
```python
from airflow import DAG
from airflow.decorators import task

dag = DAG('example')

@task
def process():
    import pandas as pd  # ✅ Only loaded during execution
    return pd.DataFrame()
```

**Why**: Airflow parses every DAG file on each scheduler heartbeat. Heavy imports add 50-200ms per file, which compounds quickly with many DAGs.

### Issue 2: Database Connection at Module Level (DL002)

**Problem**: Creating database connections during DAG parsing causes resource leaks.

**Bad**:
```python
import psycopg2

conn = psycopg2.connect(...)  # ❌ Resource leak

from airflow import DAG
```

**Good**:
```python
from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook

@task
def query():
    hook = PostgresHook(postgres_conn_id='my_db')  # ✅ Proper pattern
    conn = hook.get_conn()
    # Use connection
    conn.close()
```

**Why**: Module-level connections multiply by number of DAG files and scheduler processes, leading to connection pool exhaustion.

### Issue 3: Missing DAG Documentation (DL003)

**Problem**: DAGs without documentation are hard to understand and maintain.

**Bad**:
```python
dag = DAG('my_dag', schedule='@daily')  # ❌ No docs
```

**Good**:
```python
dag = DAG(
    'my_dag',
    schedule='@daily',
    doc_md='''  # ✅ Clear documentation
    ## Purpose
    Processes daily sales data

    ## Owner
    data-team@example.com

    ## Dependencies
    Requires sales_export DAG to complete
    '''
)
```

### Issue 4: Complex Dependencies (DL004)

**Problem**: Tasks with too many dependencies are hard to understand and debug.

**Bad**:
```python
start >> [t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11]  # ❌ Too many
```

**Good**:
```python
from airflow.utils.task_group import TaskGroup

with TaskGroup('processing') as group:  # ✅ Organized
    t1 >> t2 >> t3

start >> group
```

## Configuration

Create a `.daglinter.yml` file in your project root to customize behavior:

```yaml
version: 1

# Customize severity levels
rules:
  heavy-imports:
    enabled: true
    severity: error  # error, warning, info, off

  missing-docs:
    enabled: true
    severity: warning
    min_length: 30  # Require longer docs

# Exclude files
exclude:
  - "**/tests/**"
  - "**/__pycache__/**"
```

See the [Configuration Guide](configuration.md) for all options.

## Output Formats

### Terminal Output (Default)

Colorful, human-readable output:

```bash
daglinter dags/
```

### JSON Output

For programmatic consumption or CI/CD:

```bash
daglinter --format json dags/ > results.json
```

### SARIF Output

For GitHub Code Scanning and other security tools:

```bash
daglinter --format sarif --output results.sarif dags/
```

## CI/CD Integration

### GitHub Actions

Add to `.github/workflows/lint-dags.yml`:

```yaml
name: Lint DAGs

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
```

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: daglinter
        name: DAGLinter
        entry: daglinter
        language: system
        types: [python]
        files: ^dags/
```

Install the hook:

```bash
pip install pre-commit
pre-commit install
```

## Tips and Best Practices

1. **Start with warnings only**: Set all rules to `warning` initially, then gradually increase to `error`

2. **Use in development**: Run `daglinter` before committing to catch issues early

3. **Integrate in CI**: Add as a required check to prevent bad DAGs from merging

4. **Customize for your team**: Adjust thresholds in `.daglinter.yml` to match your standards

5. **Focus on performance rules first**: DL001 and DL002 have the biggest impact on DAG parsing speed

## Getting Help

- **Full Documentation**: See [Rule Documentation](rules.md) for detailed rule information
- **Configuration**: Check [Configuration Reference](configuration.md)
- **Examples**: Browse [Usage Examples](examples.md) for real-world scenarios
- **CLI Options**: See [CLI Reference](cli-reference.md) for all command-line options
- **Issues**: Report bugs on [GitHub Issues](https://github.com/Flossin-Tech/daglinter/issues)

## What's Next?

1. Run DAGLinter on your existing DAGs
2. Fix the errors (focus on DL001 and DL002 first for biggest performance impact)
3. Add DAGLinter to your CI/CD pipeline
4. Configure rules to match your team standards
5. Measure the performance improvement!

Happy linting! 🚀
