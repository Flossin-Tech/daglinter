# CLI Reference

Complete command-line interface documentation for DAGLinter.

## Synopsis

```bash
daglinter [OPTIONS] PATH
```

## Description

DAGLinter is a static analysis tool for Apache Airflow DAG files. It analyzes Python files to detect performance issues, anti-patterns, and maintainability problems without executing the code.

## Arguments

### Positional Arguments

#### PATH

Path to file or directory to lint.

```bash
# Lint a single file
daglinter my_dag.py

# Lint all Python files in a directory
daglinter dags/

# Lint with absolute path
daglinter /path/to/airflow/dags/
```

**Behavior**:
- If PATH is a file: Lints that file
- If PATH is a directory: Recursively lints all `.py` files
- Respects exclude patterns from configuration

## Options

### Configuration

#### --config CONFIG

Path to configuration file.

```bash
daglinter --config .daglinter.yml dags/
daglinter --config /path/to/custom-config.yml dags/
```

**Default**: Auto-discovers `.daglinter.yml` in current or parent directories

**Supported formats**: YAML (`.yml`, `.yaml`)

### Output Format

#### --format {terminal,json,sarif}

Output format for results.

```bash
# Human-readable terminal output (default)
daglinter --format terminal dags/

# Machine-readable JSON
daglinter --format json dags/

# SARIF for security tools
daglinter --format sarif dags/
```

**Options**:
- `terminal` (default): Colored, human-readable output
- `json`: JSON format for programmatic consumption
- `sarif`: SARIF 2.1.0 format for security tooling

**Example JSON Output**:
```json
{
  "version": "0.1.0",
  "scan_time": "2024-11-14T12:00:00Z",
  "summary": {
    "files_scanned": 5,
    "errors": 3,
    "warnings": 2,
    "total_violations": 5
  },
  "violations": [...]
}
```

#### --output OUTPUT

Write output to file instead of stdout.

```bash
# Write JSON to file
daglinter --format json --output results.json dags/

# Write SARIF to file
daglinter --format sarif --output results.sarif dags/
```

**Default**: Writes to stdout

**Note**: Terminal format is best viewed in stdout; use `--output` for json/sarif

### Color Output

#### --color {auto,always,never}

Control colored output.

```bash
# Auto-detect terminal support (default)
daglinter --color auto dags/

# Force colors (useful for CI logs that support ANSI)
daglinter --color always dags/

# Disable colors
daglinter --color never dags/
```

**Options**:
- `auto` (default): Enable colors if terminal supports it
- `always`: Always output colors (ANSI escape codes)
- `never`: Never output colors (plain text)

**Environment Variable**: Respects `NO_COLOR` environment variable

### Verbosity

#### --quiet, -q

Suppress informational output, only show violations.

```bash
daglinter --quiet dags/
daglinter -q dags/
```

**Effect**:
- Hides progress indicators
- Hides summary statistics
- Only shows violations
- Useful for CI/CD where you only care about failures

#### --verbose, -v

Show detailed output including debug information.

```bash
daglinter --verbose dags/
daglinter -v dags/
```

**Shows**:
- Configuration loaded
- Files being scanned
- Rules being executed
- Performance timing
- Detailed error messages

### Version and Help

#### --version

Show version information and exit.

```bash
daglinter --version
```

Output: `daglinter 0.1.0`

#### --help, -h

Show help message and exit.

```bash
daglinter --help
daglinter -h
```

## Exit Codes

DAGLinter uses standard exit codes for integration with CI/CD:

| Exit Code | Meaning | Description |
|-----------|---------|-------------|
| 0 | Success | No violations found |
| 1 | Violations found | Linting violations detected |
| 2 | Error | Tool error (invalid config, crash, etc.) |

### Examples

```bash
# Check exit code in bash
daglinter dags/
echo $?  # 0 = success, 1 = violations, 2 = error

# Use in CI/CD pipeline
daglinter dags/ || exit 1

# Fail only on errors (ignore warnings)
daglinter --format json dags/ | jq '.summary.errors > 0' && exit 1
```

## Examples

### Basic Usage

```bash
# Lint single file
daglinter my_dag.py

# Lint directory
daglinter dags/

# Lint with custom config
daglinter --config strict-config.yml dags/
```

### CI/CD Integration

```bash
# GitHub Actions
daglinter --format sarif --output results.sarif dags/

# GitLab CI (JSON report)
daglinter --format json --output daglint-report.json dags/

# Simple CI check
daglinter --quiet dags/ && echo "All DAGs passed!" || exit 1
```

### Output Formats

```bash
# Human-readable output
daglinter dags/

# Save JSON for later analysis
daglinter --format json --output results.json dags/

# Generate SARIF for GitHub Code Scanning
daglinter --format sarif --output results.sarif dags/

# Pipe JSON to jq for filtering
daglinter --format json dags/ | jq '.violations[] | select(.severity=="error")'
```

### Filtering and Processing

```bash
# Show only errors (filter warnings)
daglinter --format json dags/ | jq '.violations[] | select(.severity=="error")'

# Count violations by rule
daglinter --format json dags/ | jq '.violations | group_by(.rule_id) | map({rule: .[0].rule_id, count: length})'

# Get list of files with violations
daglinter --format json dags/ | jq -r '.violations[].file' | sort -u
```

### Combining Options

```bash
# Quiet JSON output to file
daglinter --quiet --format json --output results.json dags/

# Verbose with colors (debugging)
daglinter --verbose --color always dags/

# Strict mode with custom config
daglinter --config strict.yml --format json dags/
```

## Configuration File vs CLI

CLI arguments always override configuration file settings:

```yaml
# .daglinter.yml
output:
  format: terminal
  color: auto
```

```bash
# CLI overrides format to json
daglinter --format json dags/  # Uses JSON, not terminal

# CLI overrides color
daglinter --color never dags/  # No colors, despite auto in config
```

## Environment Variables

### NO_COLOR

Disable colored output when set to any value:

```bash
NO_COLOR=1 daglinter dags/
```

### DAGLINTER_CONFIG

Override config file location:

```bash
export DAGLINTER_CONFIG=/path/to/config.yml
daglinter dags/
```

## Common Workflows

### Local Development

```bash
# Quick check before commit
daglinter dags/my_new_dag.py

# Detailed output for debugging
daglinter --verbose dags/my_new_dag.py
```

### Pre-commit Hook

```bash
# In .git/hooks/pre-commit
#!/bin/bash
daglinter --quiet dags/ || exit 1
```

### CI/CD Pipeline

```bash
# Step 1: Lint and generate SARIF
daglinter --format sarif --output results.sarif dags/

# Step 2: Upload to GitHub Code Scanning
# (handled by GitHub Actions)

# Step 3: Also save JSON for artifacts
daglinter --format json --output results.json dags/
```

### Batch Processing

```bash
# Lint multiple directories
for dir in project1/dags project2/dags project3/dags; do
    echo "Linting $dir..."
    daglinter "$dir"
done

# Collect all results
daglinter --format json project1/dags > project1-results.json
daglinter --format json project2/dags > project2-results.json
daglinter --format json project3/dags > project3-results.json
```

## Performance Tips

### Exclude Unnecessary Files

Speed up linting by excluding irrelevant directories:

```yaml
# .daglinter.yml
exclude:
  - "**/tests/**"
  - "**/__pycache__/**"
  - "**/venv/**"
  - "**/node_modules/**"
```

### Incremental Linting

Lint only changed files in CI:

```bash
# Get changed Python files
CHANGED_FILES=$(git diff --name-only --diff-filter=d origin/main | grep "\.py$")

# Lint only changed files
if [ -n "$CHANGED_FILES" ]; then
    echo "$CHANGED_FILES" | xargs daglinter
fi
```

## Troubleshooting

### Command Not Found

```bash
# Check if daglinter is installed
which daglinter

# Check Python PATH
python -m daglinter.cli.main --version

# Reinstall if needed
pip install --force-reinstall daglinter
```

### No Output

```bash
# Use --verbose to see what's happening
daglinter --verbose dags/

# Check if files are being excluded
daglinter --verbose dags/ 2>&1 | grep "Excluding"
```

### Unexpected Violations

```bash
# See which config is being used
daglinter --verbose dags/ 2>&1 | grep "Config"

# Use explicit config
daglinter --config /dev/null dags/  # Use defaults

# Check specific rule
daglinter --format json dags/ | jq '.violations[] | select(.rule_id=="DL001")'
```

### Performance Issues

```bash
# Time the execution
time daglinter dags/

# Profile with verbose output
daglinter --verbose dags/ 2>&1 | grep -i "time\|duration"

# Reduce scope
daglinter dags/specific_dag.py  # Test single file first
```

## See Also

- [Quick Start Guide](quickstart.md) - Get started with DAGLinter
- [Configuration Reference](configuration.md) - Configuration file options
- [Rule Documentation](rules.md) - Detailed rule information
- [Examples](examples.md) - Real-world usage examples
