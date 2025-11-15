# DAGLinter Documentation

Welcome to DAGLinter - a static analysis tool for Apache Airflow DAG files that helps you catch performance issues, anti-patterns, and maintainability problems before they hit production.

## What is DAGLinter?

DAGLinter performs fast, offline static analysis using Python's AST parser to identify common issues that:
- Slow down DAG parsing
- Create resource leaks
- Make DAGs hard to maintain
- Introduce complexity

## Quick Links

### Getting Started
- [Installation Guide](user-guide/installation.md) - Get DAGLinter up and running
- [Quick Start](user-guide/quickstart.md) - Your first DAGLinter run in 5 minutes
- [Usage Examples](user-guide/examples.md) - Real-world examples and use cases

### User Documentation
- [Configuration Reference](user-guide/configuration.md) - Complete configuration options
- [Rule Documentation](user-guide/rules.md) - Detailed guide to all linting rules (DL001-DL004)
- [CLI Reference](user-guide/cli-reference.md) - Command-line interface documentation

### Developer Documentation
- [Contributing Guide](developer-guide/contributing.md) - How to contribute to DAGLinter
- [Development Setup](developer-guide/development-setup.md) - Set up your development environment
- [Architecture](developer-guide/architecture.md) - Technical architecture overview
- [Testing Guide](developer-guide/testing.md) - Testing guidelines and practices
- [Creating Rules](developer-guide/creating-rules.md) - How to create custom linting rules

### Project Information
- [Requirements](project/requirements.md) - Original project requirements
- [Implementation Roadmap](project/roadmap.md) - Development roadmap and milestones
- [Success Metrics](project/metrics.md) - How we measure success
- [User Stories](project/user-stories.md) - User stories and backlog

## Features

- **Fast Performance Analysis** - Detects heavy library imports that slow DAG parsing
- **Resource Leak Detection** - Identifies database connections created at module level
- **Documentation Quality** - Ensures DAGs have meaningful documentation
- **Complexity Analysis** - Warns about overly complex task dependency patterns
- **Multiple Output Formats** - Terminal (colored), JSON, and SARIF for CI/CD integration
- **Configurable Rules** - Customize severity levels, thresholds, and enable/disable rules
- **Zero Runtime Overhead** - Pure static analysis, never executes your code

## Rules Overview

| Rule ID | Name | Severity | Description |
|---------|------|----------|-------------|
| DL001 | Heavy Imports | ERROR | Detects heavy libraries imported at module level |
| DL002 | Database Connections | ERROR | Identifies database connections outside task context |
| DL003 | Missing Documentation | WARNING | Ensures DAGs have meaningful documentation |
| DL004 | Complex Dependencies | WARNING | Warns about excessive task fan-out/fan-in |

See the [Rule Documentation](user-guide/rules.md) for detailed information.

## Quick Example

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

## Support

- **Issues**: [GitHub Issues](https://github.com/Flossin-Tech/daglinter/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Flossin-Tech/daglinter/discussions)
- **Source Code**: [GitHub Repository](https://github.com/Flossin-Tech/daglinter)

## License

DAGLinter is released under the [MIT License](../LICENSE).
