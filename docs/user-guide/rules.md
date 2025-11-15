# Rule Documentation

DAGLinter implements four core rules to help you maintain high-quality, performant Airflow DAGs.

## Table of Contents

- [DL001: Heavy Imports at Module Level](#dl001-heavy-imports-at-module-level)
- [DL002: Database Connections at Module Level](#dl002-database-connections-at-module-level)
- [DL003: Missing DAG Documentation](#dl003-missing-dag-documentation)
- [DL004: Complex Task Dependencies](#dl004-complex-task-dependencies)

---

## DL001: Heavy Imports at Module Level

**Rule ID**: DL001
**Name**: heavy-imports
**Default Severity**: ERROR
**Category**: Performance

### Description

Detects heavy libraries (pandas, numpy, sklearn, etc.) imported at module level. These imports slow down DAG parsing because Airflow parses every DAG file on each scheduler heartbeat (typically every few seconds).

### Why It Matters

**Performance Impact**:
- Each heavy library adds 50-200ms to DAG parsing time
- With 100 DAG files, this adds 5-20 seconds per scheduler heartbeat
- Multiplied by frequent heartbeats = significant scheduler overhead
- Can cause DAG parsing timeouts and scheduler lag

**Example**: If you have 200 DAG files each importing pandas (100ms overhead), that's 20 seconds of pure import time every scheduler heartbeat.

### When It Triggers

The rule triggers when it detects module-level imports of heavy libraries:

```python
import pandas as pd              # ✗ VIOLATION
import numpy as np              # ✗ VIOLATION
from sklearn import LinearModel # ✗ VIOLATION
```

### How to Fix

Move heavy imports inside task functions:

**Before (Violation)**:
```python
import pandas as pd  # ✗ Parsed every scheduler heartbeat
import numpy as np

from airflow import DAG
from airflow.decorators import task

dag = DAG('my_dag')

@task
def process_data():
    df = pd.DataFrame({'col': [1, 2, 3]})
    return df.mean()
```

**After (Fixed)**:
```python
from airflow import DAG
from airflow.decorators import task

dag = DAG('my_dag')

@task
def process_data():
    import pandas as pd  # ✓ Only imported during task execution
    import numpy as np

    df = pd.DataFrame({'col': [1, 2, 3]})
    return df.mean()
```

### Default Heavy Libraries

DAGLinter detects these libraries by default:

| Library | Typical Import Time | Category |
|---------|-------------------|----------|
| pandas | 100-150ms | Data processing |
| numpy | 50-100ms | Numerical computing |
| sklearn | 200-300ms | Machine learning |
| tensorflow | 500-1000ms | Deep learning |
| torch | 500-1000ms | Deep learning |
| matplotlib | 100-200ms | Visualization |
| seaborn | 150-200ms | Visualization |
| plotly | 100-150ms | Visualization |
| scipy | 100-150ms | Scientific computing |
| cv2 (OpenCV) | 200-300ms | Computer vision |
| PIL | 50-100ms | Image processing |
| keras | 300-400ms | Deep learning |
| xgboost | 100-150ms | Machine learning |
| lightgbm | 100-150ms | Machine learning |

### Configuration

Add custom heavy libraries to detect:

```yaml
rules:
  heavy-imports:
    enabled: true
    severity: error
    libraries:
      - custom_heavy_lib
      - internal_ml_package
```

### Exceptions

These imports are OK at module level (lightweight):
- Standard library modules (os, sys, datetime, etc.)
- Airflow imports (airflow, airflow.operators, etc.)
- Lightweight third-party libraries

### Disable for Specific Files

Use exclude patterns in configuration:

```yaml
exclude:
  - "**/analysis_dags/**"  # Allow heavy imports in specific directories
```

---

## DL002: Database Connections at Module Level

**Rule ID**: DL002
**Name**: db-connections
**Default Severity**: ERROR
**Category**: Resource Management

### Description

Detects database connections created at module level instead of inside task context. This causes resource leaks and prevents proper connection management.

### Why It Matters

**Problems Caused**:
- **Connection Leaks**: Connections created during parsing aren't properly closed
- **Connection Pool Exhaustion**: Each scheduler process × each DAG file = many connections
- **Performance**: Opening connections during parsing slows down the scheduler
- **Security**: Connections may expose credentials in DAG file scope

**Example**: With 5 scheduler processes and 100 DAG files each creating a connection, you'd have 500 connections that are never properly closed.

### When It Triggers

The rule triggers when it detects module-level database connection calls:

```python
import psycopg2
conn = psycopg2.connect(...)  # ✗ VIOLATION

from pymongo import MongoClient
client = MongoClient(...)     # ✗ VIOLATION

import sqlalchemy
engine = sqlalchemy.create_engine(...)  # ✗ VIOLATION
```

### Detected Connection Patterns

DAGLinter detects these database connection methods:

| Database | Connection Pattern |
|----------|-------------------|
| PostgreSQL | `psycopg2.connect()` |
| MongoDB | `pymongo.MongoClient()` |
| MySQL | `mysql.connector.connect()` |
| SQLite | `sqlite3.connect()` |
| SQLAlchemy | `sqlalchemy.create_engine()` |
| SQL Server | `pymssql.connect()` |
| Oracle | `cx_Oracle.connect()` |

### How to Fix

Use Airflow Hooks inside task context:

**Before (Violation)**:
```python
import psycopg2

# ✗ Connection created at module level
conn = psycopg2.connect(
    host="localhost",
    database="airflow",
    user="user",
    password="pass"
)

from airflow import DAG
from airflow.decorators import task

dag = DAG('my_dag')

@task
def query_data():
    cursor = conn.cursor()  # Using module-level connection
    cursor.execute("SELECT * FROM my_table")
    return cursor.fetchall()
```

**After (Fixed - Using Airflow Hooks)**:
```python
from airflow import DAG
from airflow.decorators import task
from airflow.providers.postgres.hooks.postgres import PostgresHook

dag = DAG('my_dag')

@task
def query_data():
    # ✓ Connection created inside task
    hook = PostgresHook(postgres_conn_id='my_postgres')
    conn = hook.get_conn()

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM my_table")
    results = cursor.fetchall()

    conn.close()  # Properly closed
    return results
```

**Alternative (Direct Connection in Task)**:
```python
from airflow import DAG
from airflow.decorators import task

dag = DAG('my_dag')

@task
def query_data():
    # ✓ Connection created inside task (but prefer Hooks)
    import psycopg2

    conn = psycopg2.connect(
        host="localhost",
        database="airflow",
        user="user",
        password="pass"
    )

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM my_table")
        return cursor.fetchall()
    finally:
        conn.close()  # Ensure cleanup
```

### Recommended Patterns

#### PostgreSQL
```python
from airflow.providers.postgres.hooks.postgres import PostgresHook

hook = PostgresHook(postgres_conn_id='my_postgres')
records = hook.get_records("SELECT * FROM table")
```

#### MySQL
```python
from airflow.providers.mysql.hooks.mysql import MySqlHook

hook = MySqlHook(mysql_conn_id='my_mysql')
records = hook.get_records("SELECT * FROM table")
```

#### MongoDB
```python
from airflow.providers.mongo.hooks.mongo import MongoHook

hook = MongoHook(conn_id='my_mongo')
collection = hook.get_collection('my_collection')
results = collection.find({})
```

### Configuration

```yaml
rules:
  db-connections:
    enabled: true
    severity: error
```

This rule has no additional configuration options as it uses built-in detection patterns.

---

## DL003: Missing DAG Documentation

**Rule ID**: DL003
**Name**: missing-docs
**Default Severity**: WARNING
**Category**: Maintainability

### Description

Ensures DAGs have meaningful documentation. Undocumented DAGs are hard for team members to understand, maintain, and troubleshoot.

### Why It Matters

**Benefits of Good Documentation**:
- New team members can understand DAG purpose quickly
- Reduces time spent answering "what does this DAG do?"
- Helps with debugging and incident response
- Improves handoffs and knowledge transfer
- Shows up in Airflow UI for operators

### When It Triggers

The rule triggers when:
- DAG has no `doc_md` or `description` parameter
- Documentation is shorter than minimum length (default: 20 characters)
- Documentation contains placeholder text ("todo", "tbd", "fixme", etc.)

```python
# ✗ No documentation
dag = DAG('my_dag', schedule='@daily')

# ✗ Too short
dag = DAG('my_dag', doc_md='ETL', schedule='@daily')

# ✗ Placeholder text
dag = DAG('my_dag', doc_md='TODO: Add description', schedule='@daily')
```

### How to Fix

Add meaningful documentation using `doc_md` or `description`:

**Before (Violation)**:
```python
# ✗ No documentation
dag = DAG(
    'process_sales_data',
    schedule='@daily',
    start_date=datetime(2024, 1, 1)
)
```

**After (Fixed - Basic)**:
```python
# ✓ Minimal valid documentation
dag = DAG(
    'process_sales_data',
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    doc_md='Processes daily sales data from the warehouse and generates reports'
)
```

**After (Fixed - Comprehensive)**:
```python
# ✓ Comprehensive documentation (best practice)
dag = DAG(
    'process_sales_data',
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    doc_md='''
    ## Purpose
    Processes daily sales data from the data warehouse and generates
    summary reports for the business intelligence team.

    ## Schedule
    Runs daily at 2:00 AM UTC after the sales data export completes.

    ## Owner
    Data Engineering Team (data-eng@company.com)

    ## Dependencies
    - Requires `sales_export_dag` to complete successfully
    - Requires Redshift warehouse to be accessible

    ## Outputs
    - Summary tables in `analytics.daily_sales_summary`
    - CSV report uploaded to S3 bucket `s3://reports/sales/`
    - Slack notification to #data-team channel

    ## Troubleshooting
    - If sales data is missing, check `sales_export_dag` status
    - For performance issues, check Redshift query queue
    - Contact on-call: data-oncall@company.com
    '''
)
```

### Documentation Best Practices

Include these sections in your DAG documentation:

1. **Purpose**: What does this DAG do? (1-2 sentences)
2. **Schedule**: When and how often does it run?
3. **Owner**: Who owns/maintains this DAG?
4. **Dependencies**: What upstream DAGs or data sources are required?
5. **Outputs**: What does this DAG produce?
6. **Troubleshooting** (optional): Common issues and solutions

### Markdown Support

DAGLinter accepts Markdown in `doc_md`, which renders nicely in the Airflow UI:

```python
doc_md='''
# Sales Processing Pipeline

## Overview
Daily processing of sales transactions.

## Key Metrics
- **Runtime**: ~30 minutes
- **Data Volume**: ~1M rows/day
- **SLA**: Must complete by 4 AM

## Data Flow
1. Extract from CRM → S3
2. Transform in Spark
3. Load to Redshift
4. Generate reports

## Contacts
- **Owner**: Alice (alice@company.com)
- **On-call**: #data-oncall
'''
```

### Configuration

```yaml
rules:
  missing-docs:
    enabled: true
    severity: warning
    min_length: 20  # Minimum documentation length in characters
```

**Options**:
- `min_length` (default: 20): Require at least this many characters of documentation

**Examples**:
```yaml
# Require more detailed docs
rules:
  missing-docs:
    min_length: 100

# Make it an error instead of warning
rules:
  missing-docs:
    severity: error
    min_length: 50
```

### Using `description` Parameter

You can also use the `description` parameter instead of `doc_md`:

```python
dag = DAG(
    'my_dag',
    description='Processes daily sales data and generates reports',
    schedule='@daily'
)
```

**Note**: `doc_md` is preferred because:
- Supports Markdown formatting
- Allows multi-line documentation
- Renders better in Airflow UI

---

## DL004: Complex Task Dependencies

**Rule ID**: DL004
**Name**: complex-dependencies
**Default Severity**: WARNING
**Category**: Maintainability

### Description

Detects tasks with excessive fan-out (too many downstream tasks) or fan-in (too many upstream tasks). Complex dependency patterns make DAGs hard to understand, debug, and maintain.

### Why It Matters

**Problems with Complex Dependencies**:
- **Hard to Visualize**: Airflow UI becomes cluttered
- **Difficult to Debug**: Tracking failures through many dependencies is tedious
- **Performance**: Large fan-outs can overwhelm the scheduler
- **Maintenance**: Changes to one task may affect many others unexpectedly

### When It Triggers

The rule triggers when:
- A task has more than `max_fan_out` downstream dependencies (default: 10)
- A task has more than `max_fan_in` upstream dependencies (default: 10)

```python
# ✗ Excessive fan-out (>10 downstream tasks)
start >> [task1, task2, task3, task4, task5, task6, task7, task8,
          task9, task10, task11, task12]

# ✗ Excessive fan-in (>10 upstream tasks)
[task1, task2, task3, task4, task5, task6, task7, task8,
 task9, task10, task11] >> end
```

### How to Fix

Use TaskGroups to organize related tasks:

**Before (Violation)**:
```python
from airflow import DAG
from airflow.decorators import task

dag = DAG('my_dag')

@task
def start():
    return "Starting"

@task
def process_region_1(): return "Region 1"

@task
def process_region_2(): return "Region 2"

# ... 10 more similar region tasks ...

@task
def end():
    return "Complete"

# ✗ Excessive fan-out: 12 downstream tasks
with dag:
    s = start()
    r1 = process_region_1()
    r2 = process_region_2()
    # ... r3 through r12 ...
    e = end()

    s >> [r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12] >> e
```

**After (Fixed - Using TaskGroups)**:
```python
from airflow import DAG
from airflow.decorators import task
from airflow.utils.task_group import TaskGroup

dag = DAG('my_dag')

@task
def start():
    return "Starting"

@task
def process_region(region_id):
    return f"Region {region_id}"

@task
def end():
    return "Complete"

# ✓ Organized with TaskGroups
with dag:
    s = start()

    with TaskGroup("region_processing") as regions:
        # Group related tasks
        r1 = process_region(1)
        r2 = process_region(2)
        r3 = process_region(3)
        # ... etc

    e = end()

    # Clear, manageable structure
    s >> regions >> e
```

**Alternative: Dynamic Task Mapping** (Airflow 2.3+):
```python
from airflow import DAG
from airflow.decorators import task

dag = DAG('my_dag')

@task
def start():
    return "Starting"

@task
def process_region(region_id):
    return f"Processed region {region_id}"

@task
def end(results):
    return f"Processed {len(results)} regions"

# ✓ Dynamic task mapping (cleaner for many similar tasks)
with dag:
    s = start()
    regions = process_region.expand(region_id=list(range(1, 13)))
    e = end(regions)

    s >> regions >> e
```

### Organization Strategies

#### 1. Logical Grouping

Group tasks by functional area:

```python
with TaskGroup("data_validation") as validation:
    validate_schema()
    validate_quality()
    validate_completeness()

with TaskGroup("data_processing") as processing:
    clean_data()
    transform_data()
    aggregate_data()

with TaskGroup("reporting") as reporting:
    generate_report()
    send_email()
    update_dashboard()

start >> validation >> processing >> reporting >> end
```

#### 2. Hierarchical Groups

Create nested TaskGroups for complex workflows:

```python
with TaskGroup("etl") as etl:
    with TaskGroup("extract") as extract:
        extract_source_1()
        extract_source_2()

    with TaskGroup("transform") as transform:
        clean()
        join()
        aggregate()

    with TaskGroup("load") as load:
        load_to_warehouse()
        load_to_cache()

start >> etl >> end
```

#### 3. Parallel Processing Pools

For truly parallel independent tasks:

```python
# Use dynamic task mapping instead of explicit fan-out
@task
def process_file(file_path):
    # Process individual file
    pass

files = ['file1.csv', 'file2.csv', 'file3.csv', ...]
process_tasks = process_file.expand(file_path=files)

start >> process_tasks >> end
```

### Configuration

```yaml
rules:
  complex-dependencies:
    enabled: true
    severity: warning
    max_fan_out: 10  # Maximum downstream tasks per task
    max_fan_in: 10   # Maximum upstream tasks per task
```

**Options**:
- `max_fan_out` (default: 10): Threshold for downstream dependencies
- `max_fan_in` (default: 10): Threshold for upstream dependencies

**Examples**:
```yaml
# More lenient (allow larger fan-out)
rules:
  complex-dependencies:
    max_fan_out: 15
    max_fan_in: 15

# Stricter (enforce tighter organization)
rules:
  complex-dependencies:
    max_fan_out: 5
    max_fan_in: 5
    severity: error
```

### When High Fan-out is Acceptable

Some patterns naturally have high fan-out:
- **Broadcast patterns**: One result fanning out to many consumers
- **Notification patterns**: Sending alerts to multiple channels
- **Parallel independent tasks**: Genuinely independent operations

For these cases:
1. Document why high fan-out is necessary
2. Consider if TaskGroups could still improve clarity
3. Or adjust the threshold in configuration for specific DAGs

### Best Practices

1. **Use TaskGroups**: Group related tasks logically
2. **Dynamic Task Mapping**: Use `.expand()` for many similar tasks
3. **Intermediate Tasks**: Add aggregation tasks between layers
4. **SubDAGs** (deprecated): Prefer TaskGroups over SubDAGs
5. **Documentation**: Explain complex dependency patterns

---

## Global Rule Configuration

### Disabling Rules Globally

```yaml
rules:
  heavy-imports:
    enabled: false  # Disable completely
```

### Adjusting Severity

```yaml
rules:
  missing-docs:
    severity: error  # Make warnings into errors

  complex-dependencies:
    severity: info   # Downgrade to informational
```

### Excluding Files from Specific Rules

Use file exclusion patterns:

```yaml
exclude:
  - "**/legacy_dags/**"      # Exclude all legacy DAGs
  - "**/experimental/**"      # Exclude experimental DAGs
  - "**/tests/**"            # Exclude test DAGs
```

## See Also

- [Configuration Reference](configuration.md) - Detailed configuration options
- [Quick Start](quickstart.md) - Get started with DAGLinter
- [Examples](examples.md) - Real-world usage examples
- [CLI Reference](cli-reference.md) - Command-line options
