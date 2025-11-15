# Usage Examples

Real-world examples showing DAGLinter in action.

## Table of Contents

- [Example 1: Clean DAG (No Violations)](#example-1-clean-dag-no-violations)
- [Example 2: Multiple Violations](#example-2-multiple-violations)
- [Example 3: Database Connection Issues](#example-3-database-connection-issues)
- [Example 4: Complex Dependencies](#example-4-complex-dependencies)
- [Example 5: JSON Output for CI/CD](#example-5-json-output-for-cicd)
- [Example 6: SARIF Output for Code Scanning](#example-6-sarif-output-for-code-scanning)
- [Example 7: Using Configuration Files](#example-7-using-configuration-files)
- [Example 8: Directory Scanning](#example-8-directory-scanning)
- [Example 9: CI/CD Integration](#example-9-cicd-integration)

---

## Example 1: Clean DAG (No Violations)

A well-written Airflow DAG that follows all best practices.

### DAG Code

**File:** `good_dag.py`

```python
"""
A well-written Airflow DAG that follows best practices.
"""

from datetime import datetime
from airflow import DAG
from airflow.decorators import task

# Good: Standard library imports at top
from airflow.operators.python import PythonOperator

dag = DAG(
    'good_example_dag',
    description='Example DAG following best practices',
    doc_md="""
    ## Purpose
    This DAG demonstrates proper Airflow patterns:
    - Imports heavy libraries inside tasks
    - Documents the DAG purpose
    - Uses simple dependency patterns
    - Database connections via Airflow hooks
    """,
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
)

@task
def process_data():
    # Good: Heavy imports inside the task
    import pandas as pd
    import numpy as np

    data = pd.DataFrame({'values': np.random.rand(100)})
    return data.mean().values[0]

@task
def query_database():
    # Good: Use Airflow connections instead of direct DB calls
    from airflow.providers.postgres.hooks.postgres import PostgresHook

    hook = PostgresHook('my_postgres_conn')
    result = hook.get_records("SELECT * FROM my_table LIMIT 10")
    return len(result)

# Good: Simple, clear dependency pattern
with dag:
    data = process_data()
    db_result = query_database()
    data >> db_result
```

### DAGLinter Output

```bash
$ daglinter good_dag.py

✓ All 1 file(s) passed linting!
```

**Exit Code:** 0 (Success)

**Why it passes:**
- Heavy imports (pandas, numpy) are inside task functions
- DAG has comprehensive documentation
- Uses Airflow Hooks for database connections
- Simple, clear dependency pattern

---

## Example 2: Multiple Violations

Example showing multiple anti-patterns in a single DAG.

### DAG Code

**File:** `bad_imports.py`

```python
"""
Example of a poorly written DAG with multiple anti-patterns.
"""

from datetime import datetime
from airflow import DAG
import pandas as pd  # ❌ DL001: Heavy import at module level
import numpy as np   # ❌ DL001: Heavy import at module level
from sklearn.ensemble import RandomForestClassifier  # ❌ DL001

from airflow.decorators import task

# ❌ DL003: Missing meaningful documentation
dag = DAG(
    'bad_example_dag',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
)

@task
def process_data():
    data = pd.DataFrame({'values': np.random.rand(100)})
    return data.mean().values[0]
```

### DAGLinter Output

```bash
$ daglinter bad_imports.py

Linting Results
────────────────────────────────────────────────────────────

bad_imports.py
  ✗ DL001 ERROR (line 6:0)
    Heavy import 'pandas' at module level may slow DAG parsing
    → import pandas as pd
    Suggestion: Move 'import pandas' inside your task function...

  ✗ DL001 ERROR (line 7:0)
    Heavy import 'numpy' at module level may slow DAG parsing
    → import numpy as np
    Suggestion: Move 'import numpy' inside your task function...

  ✗ DL001 ERROR (line 8:0)
    Heavy import 'sklearn.ensemble' at module level
    → from sklearn.ensemble import RandomForestClassifier
    Suggestion: Move 'import sklearn.ensemble' inside...

  ⚠ DL003 WARNING (line 13:6)
    DAG missing meaningful documentation
    → dag = DAG(
    Suggestion: Add doc_md parameter with DAG purpose...

────────────────────────────────────────────────────────────
Summary
  Files scanned: 1
  Files with issues: 1
  ✗ Errors: 3
  ⚠ Warnings: 1

✗ Linting failed with 3 error(s)
```

**Exit Code:** 1 (Violations Found)

### How to Fix

```python
from datetime import datetime
from airflow import DAG
from airflow.decorators import task

# ✓ Good: Meaningful documentation
dag = DAG(
    'fixed_example_dag',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    doc_md="""
    ## Purpose
    Processes daily data using ML models

    ## Owner
    Data Science Team
    """
)

@task
def process_data():
    # ✓ Good: Heavy imports inside task
    import pandas as pd
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier

    data = pd.DataFrame({'values': np.random.rand(100)})
    return data.mean().values[0]
```

---

## Example 3: Database Connection Issues

Detecting database connections at module level.

### DAG Code

**File:** `bad_db_connection.py`

```python
from datetime import datetime
from airflow import DAG
from airflow.decorators import task
import psycopg2

# ❌ DL002: Database connection at module level
conn = psycopg2.connect(
    host="localhost",
    database="airflow",
    user="user",
    password="pass"
)

dag = DAG(
    'db_connection_dag',
    doc_md="DAG demonstrating database connection issues",
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
)

@task
def query_data():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM my_table")
    return cursor.fetchall()
```

### DAGLinter Output

```bash
$ daglinter bad_db_connection.py

Linting Results
────────────────────────────────────────────────────────────

bad_db_connection.py
  ✗ DL002 ERROR (line 6:0)
    Database connection 'psycopg2.connect' at module level
    → conn = psycopg2.connect(
    Suggestion: Use Airflow connection hooks...

────────────────────────────────────────────────────────────
Summary
  Files scanned: 1
  ✗ Errors: 1

✗ Linting failed with 1 error(s)
```

### How to Fix

```python
from airflow import DAG
from airflow.decorators import task
from airflow.providers.postgres.hooks.postgres import PostgresHook

dag = DAG(
    'db_connection_dag',
    doc_md="DAG with proper database connection handling",
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
)

@task
def query_data():
    # ✓ Good: Use Airflow Hook
    hook = PostgresHook(postgres_conn_id='my_postgres')
    return hook.get_records("SELECT * FROM my_table")
```

---

## Example 4: Complex Dependencies

Detecting overly complex dependency patterns.

### DAG Code

**File:** `complex_dependencies.py`

```python
from datetime import datetime
from airflow import DAG
from airflow.decorators import task

dag = DAG(
    'complex_dag',
    doc_md="DAG with complex dependencies",
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
)

@task
def start(): return "start"

@task
def process_1(): return "p1"

@task
def process_2(): return "p2"

# ... define process_3 through process_12 ...

@task
def end(): return "end"

# ❌ DL004: Too many downstream dependencies (12 tasks)
with dag:
    s = start()
    tasks = [process_1(), process_2(), ...]  # 12 tasks
    e = end()

    s >> tasks >> e  # 12 downstream from start
```

### DAGLinter Output

```bash
$ daglinter complex_dependencies.py

Linting Results
────────────────────────────────────────────────────────────

complex_dependencies.py
  ⚠ DL004 WARNING (line 25:4)
    Task 'start' has 12 downstream dependencies (max: 10)
    → s >> tasks
    Suggestion: Use TaskGroup to organize tasks...

────────────────────────────────────────────────────────────
Summary
  Files scanned: 1
  ⚠ Warnings: 1

⚠ Found 1 warning(s) but no errors
```

### How to Fix

```python
from airflow import DAG
from airflow.decorators import task
from airflow.utils.task_group import TaskGroup

dag = DAG('organized_dag', doc_md="Well-organized DAG")

@task
def start(): return "start"

@task
def process(group_id, task_id):
    return f"{group_id}_{task_id}"

@task
def end(): return "end"

# ✓ Good: Organized with TaskGroups
with dag:
    s = start()

    with TaskGroup("group_1") as g1:
        [process("g1", i) for i in range(6)]

    with TaskGroup("group_2") as g2:
        [process("g2", i) for i in range(6)]

    e = end()

    s >> [g1, g2] >> e  # Only 2 downstream tasks!
```

---

## Example 5: JSON Output for CI/CD

Using JSON format for programmatic processing.

### Command

```bash
daglinter --format json dags/ > results.json
```

### JSON Output

```json
{
  "version": "0.1.0",
  "scan_time": "2024-11-14T21:18:04.517951Z",
  "summary": {
    "files_scanned": 5,
    "errors": 3,
    "warnings": 2,
    "info": 0,
    "total_violations": 5
  },
  "violations": [
    {
      "file": "dags/bad_imports.py",
      "line": 6,
      "column": 0,
      "severity": "error",
      "rule_id": "DL001",
      "rule_name": "heavy-imports",
      "message": "Heavy import 'pandas' at module level",
      "suggestion": "Move 'import pandas' inside your task...",
      "code_snippet": "import pandas as pd"
    },
    {
      "file": "dags/missing_docs.py",
      "line": 10,
      "column": 6,
      "severity": "warning",
      "rule_id": "DL003",
      "rule_name": "missing-docs",
      "message": "DAG missing meaningful documentation",
      "suggestion": "Add doc_md parameter...",
      "code_snippet": "dag = DAG('test')"
    }
  ]
}
```

### Processing with jq

```bash
# Count errors
cat results.json | jq '.summary.errors'

# List files with violations
cat results.json | jq -r '.violations[].file' | sort -u

# Get only errors (filter warnings)
cat results.json | jq '.violations[] | select(.severity=="error")'

# Group by rule
cat results.json | jq '.violations | group_by(.rule_id)'
```

---

## Example 6: SARIF Output for Code Scanning

SARIF format for GitHub Code Scanning and security tools.

### Command

```bash
daglinter --format sarif --output results.sarif dags/
```

### SARIF Output

```json
{
  "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "DAGLinter",
          "version": "0.1.0",
          "informationUri": "https://github.com/Flossin-Tech/daglinter",
          "rules": [
            {
              "id": "DL001",
              "name": "heavy-imports",
              "shortDescription": {
                "text": "Heavy imports at module level"
              },
              "helpUri": "https://daglinter.io/rules/DL001"
            }
          ]
        }
      },
      "results": [
        {
          "ruleId": "DL001",
          "level": "error",
          "message": {
            "text": "Heavy import 'pandas' at module level"
          },
          "locations": [
            {
              "physicalLocation": {
                "artifactLocation": {
                  "uri": "dags/bad_imports.py"
                },
                "region": {
                  "startLine": 6,
                  "startColumn": 0
                }
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### GitHub Actions Integration

```yaml
- name: Run DAGLinter
  run: daglinter dags/ --format sarif --output results.sarif

- name: Upload SARIF to GitHub
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: results.sarif
```

---

## Example 7: Using Configuration Files

Customizing DAGLinter behavior with configuration.

### Configuration File

**File:** `.daglinter.yml`

```yaml
version: 1

# Exclude patterns
exclude:
  - "**/tests/**"
  - "**/__pycache__/**"
  - "**/examples/**"

# Rule configurations
rules:
  heavy-imports:
    enabled: true
    severity: error
    libraries:
      # Default libraries plus custom ones
      - custom_ml_lib
      - company_data_package

  db-connections:
    enabled: true
    severity: error

  missing-docs:
    enabled: true
    severity: warning
    min_length: 50  # Require longer documentation

  complex-dependencies:
    enabled: true
    severity: warning
    max_fan_out: 8  # Stricter than default 10
    max_fan_in: 8
```

### Usage

```bash
# Auto-discovers .daglinter.yml
daglinter dags/

# Or specify explicit config
daglinter --config custom-config.yml dags/
```

---

## Example 8: Directory Scanning

Scanning multiple DAG files at once.

### Directory Structure

```
dags/
├── ingestion/
│   ├── sales_dag.py          (clean)
│   └── customer_dag.py       (has violations)
├── transformation/
│   ├── etl_dag.py           (has violations)
│   └── aggregation_dag.py   (clean)
└── reporting/
    └── dashboard_dag.py     (has violations)
```

### Command

```bash
daglinter dags/
```

### Output

```
Linting Results
────────────────────────────────────────────────────────────

dags/ingestion/customer_dag.py
  ✗ DL001 ERROR (line 5:0)
    Heavy import 'pandas' at module level
    ...

dags/transformation/etl_dag.py
  ✗ DL001 ERROR (line 8:0)
    Heavy import 'numpy' at module level
    ...
  ⚠ DL003 WARNING (line 15:6)
    DAG missing meaningful documentation
    ...

dags/reporting/dashboard_dag.py
  ✗ DL002 ERROR (line 10:0)
    Database connection at module level
    ...

────────────────────────────────────────────────────────────
Summary
  Files scanned: 5
  Files with issues: 3
  ✗ Errors: 3
  ⚠ Warnings: 1

✗ Linting failed with 3 error(s)
```

---

## Example 9: CI/CD Integration

Complete CI/CD workflow examples.

### GitHub Actions

**File:** `.github/workflows/lint-dags.yml`

```yaml
name: Lint Airflow DAGs

on:
  pull_request:
    paths:
      - 'dags/**'
  push:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install DAGLinter
        run: pip install daglinter

      - name: Lint DAGs (Terminal Output)
        run: daglinter dags/

      - name: Generate SARIF Report
        if: always()
        run: daglinter dags/ --format sarif --output results.sarif

      - name: Upload SARIF to GitHub
        if: always()
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: results.sarif

      - name: Generate JSON Report
        if: always()
        run: daglinter dags/ --format json --output results.json

      - name: Upload Artifact
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: daglint-results
          path: results.json
```

### GitLab CI

**File:** `.gitlab-ci.yml`

```yaml
daglint:
  image: python:3.10
  stage: test
  script:
    - pip install daglinter
    - daglinter --format json dags/ > daglint-report.json
  artifacts:
    reports:
      codequality: daglint-report.json
    paths:
      - daglint-report.json
  only:
    changes:
      - dags/**
```

### Pre-commit Hook

**File:** `.pre-commit-config.yaml`

```yaml
repos:
  - repo: local
    hooks:
      - id: daglinter
        name: Lint Airflow DAGs
        entry: daglinter
        language: system
        types: [python]
        files: ^dags/
        pass_filenames: true
```

**Installation:**

```bash
pip install pre-commit
pre-commit install

# Now runs automatically on git commit
git add dags/my_dag.py
git commit -m "Add new DAG"  # DAGLinter runs automatically
```

---

## Tips and Tricks

### Lint Only Changed Files

```bash
# Get changed files in git
CHANGED=$(git diff --name-only --diff-filter=d HEAD | grep "^dags/.*\.py$")

# Lint only those files
if [ -n "$CHANGED" ]; then
    echo "$CHANGED" | xargs daglinter
fi
```

### Progressive Enhancement

Start lenient, get stricter over time:

**Week 1** (`.daglinter-week1.yml`):
```yaml
rules:
  heavy-imports:
    severity: warning  # Just warn initially
  missing-docs:
    enabled: false     # Disabled for now
```

**Week 4** (`.daglinter-week4.yml`):
```yaml
rules:
  heavy-imports:
    severity: error    # Now enforce
  missing-docs:
    severity: warning  # Start requiring
    min_length: 20
```

### Fail Fast in CI

```bash
# Fail on first error for faster feedback
daglinter --quiet dags/ || exit 1
```

### Generate Reports

```bash
# Create detailed report
daglinter --format json dags/ | jq '.' > report-$(date +%Y%m%d).json
```

## See Also

- [Quick Start Guide](quickstart.md)
- [Configuration Reference](configuration.md)
- [Rule Documentation](rules.md)
- [CLI Reference](cli-reference.md)
