# Configuration Reference

DAGLinter can be configured using a `.daglinter.yml` file or command-line arguments.

## Configuration File

Create a `.daglinter.yml` file in your project root or any parent directory. DAGLinter will automatically discover it.

### Basic Example

```yaml
version: 1

# Exclude patterns
exclude:
  - "**/tests/**"
  - "**/__pycache__/**"
  - "**/venv/**"

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

## Configuration Options

### Top-Level Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `version` | integer | 1 | Configuration file version |
| `exclude` | list | [] | Glob patterns to exclude from linting |
| `rules` | dict | {} | Rule-specific configurations |
| `output` | dict | {} | Output formatting options |

### Exclude Patterns

Exclude files or directories using glob patterns:

```yaml
exclude:
  - "**/tests/**"           # All test directories
  - "**/__pycache__/**"     # Python cache
  - "**/venv/**"            # Virtual environments
  - "**/node_modules/**"    # Node modules
  - "examples/**"           # Example DAGs
  - "**/*.bak"              # Backup files
```

**Note**: Patterns are matched using Python's `pathlib.Path.match()` with glob syntax.

## Rule Configuration

Each rule can be configured individually under the `rules` section.

### Common Rule Options

All rules support these options:

| Option | Type | Values | Description |
|--------|------|--------|-------------|
| `enabled` | boolean | true/false | Enable or disable the rule |
| `severity` | string | error/warning/info | Severity level for violations |

### Rule: heavy-imports (DL001)

Detects heavy libraries imported at module level.

```yaml
rules:
  heavy-imports:
    enabled: true
    severity: error
    libraries:
      # Default heavy libraries
      - pandas
      - numpy
      - sklearn
      - tensorflow
      - torch
      - matplotlib
      - seaborn
      - plotly
      - scipy
      # Add your custom heavy libraries
      - custom_ml_lib
      - internal_data_lib
```

**Options**:
- `libraries` (list): Additional libraries to consider heavy. Extends the default list.

**Default heavy libraries**:
- pandas, numpy, sklearn, tensorflow, torch, matplotlib, seaborn, plotly, scipy, cv2, PIL, keras, xgboost, lightgbm

### Rule: db-connections (DL002)

Detects database connections outside task context.

```yaml
rules:
  db-connections:
    enabled: true
    severity: error
```

**Detected connection patterns**:
- `psycopg2.connect()`
- `pymongo.MongoClient()`
- `mysql.connector.connect()`
- `sqlite3.connect()`
- `sqlalchemy.create_engine()`
- `pymssql.connect()`
- `cx_Oracle.connect()`

**Options**: None (uses built-in patterns)

### Rule: missing-docs (DL003)

Ensures DAGs have meaningful documentation.

```yaml
rules:
  missing-docs:
    enabled: true
    severity: warning
    min_length: 20  # Minimum documentation length
```

**Options**:
- `min_length` (integer, default: 20): Minimum number of characters required in documentation

**Documentation sources checked**:
- `doc_md` parameter
- `description` parameter

**Rejected as valid documentation**:
- Empty strings
- Strings shorter than `min_length`
- Placeholder text: "todo", "tbd", "fixme", "xxx", "placeholder"

### Rule: complex-dependencies (DL004)

Warns about overly complex task dependency patterns.

```yaml
rules:
  complex-dependencies:
    enabled: true
    severity: warning
    max_fan_out: 10  # Max downstream tasks per task
    max_fan_in: 10   # Max upstream tasks per task
```

**Options**:
- `max_fan_out` (integer, default: 10): Maximum number of downstream dependencies per task
- `max_fan_in` (integer, default: 10): Maximum number of upstream dependencies per task

## Output Configuration

Configure output formatting and behavior:

```yaml
output:
  format: terminal       # terminal, json, or sarif
  color: auto           # auto, always, or never
  quiet: false          # Suppress non-essential output
  verbose: false        # Show detailed output
```

### Output Options

| Option | Type | Values | Description |
|--------|------|--------|-------------|
| `format` | string | terminal/json/sarif | Output format |
| `color` | string | auto/always/never | Color output mode |
| `quiet` | boolean | true/false | Suppress informational messages |
| `verbose` | boolean | true/false | Show detailed information |

## CLI Override

Command-line arguments always take precedence over configuration file settings.

```bash
# Override format
daglinter --format json dags/

# Override color
daglinter --color never dags/

# Specify explicit config file
daglinter --config custom-config.yml dags/
```

## Configuration Discovery

DAGLinter searches for configuration files in this order:

1. Explicit path via `--config` argument
2. `.daglinter.yml` in current directory
3. `.daglinter.yml` in parent directories (up to root)
4. Built-in defaults if no config found

## Complete Example

```yaml
version: 1

# Exclude patterns
exclude:
  - "**/tests/**"
  - "**/__pycache__/**"
  - "**/venv/**"
  - "**/build/**"
  - "**/dist/**"

# Rule configurations
rules:
  heavy-imports:
    enabled: true
    severity: error
    libraries:
      # Data processing
      - pandas
      - numpy
      - polars
      # ML libraries
      - sklearn
      - tensorflow
      - torch
      - xgboost
      # Visualization
      - matplotlib
      - seaborn
      - plotly
      # Custom libraries
      - company_data_lib

  db-connections:
    enabled: true
    severity: error

  missing-docs:
    enabled: true
    severity: warning
    min_length: 50  # Require more detailed docs

  complex-dependencies:
    enabled: true
    severity: warning
    max_fan_out: 8   # Stricter than default
    max_fan_in: 8

# Output settings
output:
  format: terminal
  color: auto
  verbose: false
  quiet: false
```

## Severity Levels

| Level | Behavior | Use Case |
|-------|----------|----------|
| `error` | Fails linting (exit code 1) | Critical issues that must be fixed |
| `warning` | Shows warning but doesn't fail | Issues that should be reviewed |
| `info` | Informational only | Suggestions for improvement |

## Disabling Rules

To completely disable a rule:

```yaml
rules:
  missing-docs:
    enabled: false
```

Or change severity to make it less strict:

```yaml
rules:
  heavy-imports:
    severity: warning  # Downgrade from error to warning
```

## Environment-Specific Configuration

You can maintain different configurations for different environments:

```bash
# Development (lenient)
daglinter --config .daglinter-dev.yml dags/

# CI/CD (strict)
daglinter --config .daglinter-ci.yml dags/
```

**Example: Development Config** (`.daglinter-dev.yml`):
```yaml
rules:
  heavy-imports:
    severity: warning  # Allow heavy imports in dev
  missing-docs:
    enabled: false     # Don't require docs in dev
```

**Example: CI Config** (`.daglinter-ci.yml`):
```yaml
rules:
  heavy-imports:
    severity: error    # Strict in CI
  missing-docs:
    severity: error    # Require docs in CI
    min_length: 50
```

## Validation

DAGLinter validates your configuration file on startup. If there are errors, you'll see:

```
Configuration error: Invalid severity 'critical' for rule 'heavy-imports'
Valid values: error, warning, info
```

## Best Practices

1. **Version control your config**: Commit `.daglinter.yml` to git
2. **Start lenient, get stricter**: Begin with warnings, gradually move to errors
3. **Document custom libraries**: Comment why libraries are in the heavy list
4. **Team agreement**: Ensure the team agrees on severity levels
5. **Review regularly**: Update configuration as patterns evolve

## Troubleshooting

### Config not being found

```bash
# Check current directory
ls -la .daglinter.yml

# Check parent directories
find .. -name ".daglinter.yml"

# Use explicit path
daglinter --config path/to/.daglinter.yml dags/
```

### Rules not applying

1. Check rule name matches exactly (case-sensitive)
2. Verify rule is enabled: `enabled: true`
3. Check exclude patterns aren't excluding your files
4. Use `--verbose` to see which config is loaded

### Syntax errors

Ensure valid YAML syntax:
```bash
# Validate YAML
python -c "import yaml; yaml.safe_load(open('.daglinter.yml'))"
```

## See Also

- [Rule Documentation](rules.md) - Detailed rule information
- [CLI Reference](cli-reference.md) - Command-line options
- [Examples](examples.md) - Configuration examples
