# Contributing to DAGLinter

Thank you for your interest in contributing to DAGLinter! We welcome contributions of all kinds, from bug reports and documentation improvements to new features and rule implementations.

## Quick Links

📖 **Full Contributing Guide**: [docs/developer-guide/contributing.md](docs/developer-guide/contributing.md)

📚 **Developer Documentation**:
- [Development Setup](docs/developer-guide/development-setup.md) - Set up your development environment
- [Testing Guide](docs/developer-guide/testing.md) - Testing guidelines and practices
- [Creating Rules](docs/developer-guide/creating-rules.md) - How to create custom linting rules
- [Architecture](docs/developer-guide/architecture.md) - Technical architecture overview

## Quick Start

### 1. Fork and Clone

```bash
# Fork on GitHub, then:
git clone https://github.com/YOUR_USERNAME/daglinter.git
cd daglinter
git remote add upstream https://github.com/Flossin-Tech/daglinter.git
```

### 2. Set Up Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### 3. Make Changes

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes
# Write tests
# Update documentation
```

### 4. Run Tests and Checks

```bash
# Run tests
pytest

# Check formatting
black --check src/ tests/

# Run linter
ruff check src/ tests/

# Type checking
mypy src/

# Check coverage
pytest --cov=daglinter --cov-report=term-missing
```

### 5. Submit Pull Request

```bash
# Commit your changes
git add .
git commit -m "feat: your feature description"

# Push to your fork
git push origin feature/your-feature-name

# Create Pull Request on GitHub
```

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please be:

- Respectful and considerate
- Collaborative and constructive
- Focused on what's best for the community

## Ways to Contribute

### Reporting Bugs

- Use [GitHub Issues](https://github.com/Flossin-Tech/daglinter/issues)
- Include minimal reproducible example
- Specify Python version and environment
- Describe expected vs actual behavior

### Suggesting Features

- Open a [GitHub Discussion](https://github.com/Flossin-Tech/daglinter/discussions) first
- Explain the use case and benefit
- Propose an implementation approach
- Be open to feedback

### Writing Code

Look for issues labeled:
- `good-first-issue` - Great for newcomers
- `help-wanted` - Community contributions needed
- `bug` - Bug fixes
- `enhancement` - New features

### Improving Documentation

- Fix typos or unclear explanations
- Add examples and tutorials
- Improve code comments
- Translate documentation

## Development Standards

### Code Style

- **Formatter**: Black (line length 88)
- **Linter**: Ruff
- **Type Checking**: MyPy
- **Docstrings**: Google style

### Test Requirements

- Minimum 85% overall coverage
- 100% coverage for new features
- Unit tests for all new code
- Integration tests for features

### Commit Messages

Follow conventional commits:

```
<type>: <short summary>

<detailed description>

<footer>
```

**Types**: feat, fix, docs, style, refactor, test, chore

**Example**:
```
feat: add DL005 missing timeout rule

Implement rule to detect tasks without execution_timeout
configured. Helps prevent tasks from hanging indefinitely.

Closes #123
```

## Pull Request Process

1. **Update Documentation**: Add/update docstrings, README, and guides
2. **Add Tests**: Maintain/improve coverage
3. **Run Checks**: Ensure all tests and linting pass
4. **Describe Changes**: Clear PR description with context
5. **Review**: Address feedback from maintainers
6. **Merge**: Maintainer will merge when approved

## Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/unit/test_parser.py::test_specific

# With coverage
pytest --cov=daglinter --cov-report=html

# View coverage
open htmlcov/index.html
```

## Getting Help

- **Questions**: [GitHub Discussions](https://github.com/Flossin-Tech/daglinter/discussions)
- **Bugs**: [GitHub Issues](https://github.com/Flossin-Tech/daglinter/issues)
- **Documentation**: [docs/](docs/) directory

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- GitHub contributors page

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to DAGLinter! Every contribution, no matter how small, helps make this tool better for the entire Airflow community. 🚀

For detailed guidelines, see the [Full Contributing Guide](docs/developer-guide/contributing.md).
