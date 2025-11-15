# Installation Guide

This guide covers all the ways to install DAGLinter.

## Prerequisites

- Python 3.8 or higher
- pip or your preferred Python package manager

DAGLinter has minimal dependencies and does not require Apache Airflow to be installed. It works completely offline using static analysis.

## Installation Methods

### Via pip (Recommended)

Once DAGLinter is published to PyPI, install it using pip:

```bash
pip install daglinter
```

To upgrade to the latest version:

```bash
pip install --upgrade daglinter
```

### From Source

For development or to use the latest features:

```bash
# Clone the repository
git clone https://github.com/Flossin-Tech/daglinter.git
cd daglinter

# Install in editable mode
pip install -e .
```

For development with all dev dependencies:

```bash
pip install -e ".[dev]"
```

### In a Virtual Environment (Recommended)

Always install in a virtual environment to avoid dependency conflicts:

```bash
# Create virtual environment
python -m venv daglinter-env

# Activate (Linux/macOS)
source daglinter-env/bin/activate

# Activate (Windows)
daglinter-env\Scripts\activate

# Install DAGLinter
pip install daglinter
```

### With pipx (Isolated Installation)

Install DAGLinter in an isolated environment using pipx:

```bash
# Install pipx if you don't have it
pip install pipx

# Install DAGLinter
pipx install daglinter
```

## Verify Installation

After installation, verify DAGLinter is working:

```bash
# Check version
daglinter --version

# Show help
daglinter --help
```

You should see output similar to:

```
daglinter 0.1.0
```

## Dependencies

DAGLinter has minimal dependencies:

- **rich** (>=13.0.0) - Terminal formatting and colored output
- **pyyaml** (>=6.0) - Configuration file parsing
- **typing-extensions** (>=4.0.0) - Python 3.8 compatibility

All dependencies are automatically installed when you install DAGLinter.

## IDE Integration

### VS Code

For VS Code integration (future feature):

```bash
# Install VS Code extension (coming soon)
code --install-extension daglinter.vscode-daglinter
```

### PyCharm

DAGLinter can be added as an external tool in PyCharm:

1. Go to Settings > Tools > External Tools
2. Click "+" to add a new tool
3. Configure:
   - Name: DAGLinter
   - Program: `daglinter` (or full path)
   - Arguments: `$FilePath$`
   - Working directory: `$ProjectFileDir$`

## Uninstallation

To remove DAGLinter:

```bash
# If installed via pip
pip uninstall daglinter

# If installed via pipx
pipx uninstall daglinter
```

## Troubleshooting

### Command not found

If you get "command not found" after installation:

1. Ensure your Python scripts directory is in PATH
2. On Linux/macOS, add to ~/.bashrc or ~/.zshrc:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```
3. On Windows, Python scripts are usually in `C:\PythonXX\Scripts\`

### Permission Errors

If you encounter permission errors:

```bash
# Use --user flag
pip install --user daglinter

# Or use a virtual environment (recommended)
python -m venv venv
source venv/bin/activate
pip install daglinter
```

### Import Errors

If you get import errors after installation:

1. Ensure you're using Python 3.8 or higher: `python --version`
2. Try reinstalling: `pip install --force-reinstall daglinter`
3. Check for conflicting packages: `pip list | grep daglinter`

## Next Steps

- Read the [Quick Start Guide](quickstart.md) to start using DAGLinter
- Configure DAGLinter using [Configuration Guide](configuration.md)
- Learn about all rules in [Rule Documentation](rules.md)
