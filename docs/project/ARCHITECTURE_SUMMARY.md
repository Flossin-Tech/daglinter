# DAGLinter Architecture - Quick Reference

## Document Navigation

| Document | Purpose | Key Audience |
|----------|---------|--------------|
| **[TECHNICAL_ARCHITECTURE.md](./TECHNICAL_ARCHITECTURE.md)** | Detailed implementation specifications | Engineers building MVP |
| **[REQUIREMENTS.md](./REQUIREMENTS.md)** | Complete requirements specification | Product, Engineering, QA |
| **[IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md)** | 8-week delivery plan and milestones | All stakeholders |
| **[USER_STORIES_BACKLOG.md](./USER_STORIES_BACKLOG.md)** | Sprint-ready user stories with estimates | Engineering, Product |
| **[SUCCESS_METRICS.md](./SUCCESS_METRICS.md)** | KPIs and measurement framework | Leadership, Product |

---

## Architecture At-a-Glance

### System Components

```
CLI Entry → Config Loader → File Scanner → AST Parser → Rule Engine → Formatters
                                              ↓              ↓
                                          Parse Tree    Violations
```

### Core Technologies

- **Language**: Python 3.8+
- **Parsing**: stdlib `ast` module
- **CLI**: `argparse` (stdlib)
- **Terminal UI**: `rich` library
- **Config**: `pyyaml`
- **Testing**: `pytest` + `pytest-cov`

### MVP Rules (4 Total)

| Rule ID | Name | Severity | Detects |
|---------|------|----------|---------|
| DL001 | heavy-imports | ERROR | pandas, numpy at module level |
| DL002 | db-connections | ERROR | Database connections outside tasks |
| DL003 | missing-docs | WARNING | DAGs without documentation |
| DL004 | complex-dependencies | WARNING | >10 fan-out/in, >5 depth |

---

## File Structure

```
daglinter/
├── daglinter/              # Main package
│   ├── cli/                # CLI components
│   ├── core/               # AST parser, config, linter
│   ├── rules/              # Linting rules
│   ├── formatters/         # Output formats (terminal/JSON/SARIF)
│   └── utils/              # Helpers
├── tests/
│   ├── unit/               # Unit tests (70%)
│   ├── integration/        # Integration tests (25%)
│   └── fixtures/           # Test DAG files
├── docs/                   # Rule documentation
└── examples/               # Config examples
```

---

## Implementation Checklist

### Week 1-2: Foundation
- [ ] AST parser with error handling
- [ ] Base rule class and registry
- [ ] HeavyImportRule (DL001)
- [ ] DatabaseConnectionRule (DL002)
- [ ] Unit tests (≥85% coverage)

### Week 3-4: Core Features
- [ ] MissingDocsRule (DL003)
- [ ] ComplexDependencyRule (DL004)
- [ ] CLI with argparse
- [ ] Terminal formatter (Rich)
- [ ] File scanner
- [ ] Integration tests

### Week 5-6: Configuration & Integration
- [ ] .daglinter.yml support
- [ ] JSON formatter
- [ ] SARIF formatter
- [ ] Exit codes
- [ ] Performance benchmarks

### Week 7-8: Polish & Release
- [ ] Cross-platform testing
- [ ] Documentation
- [ ] CI/CD examples
- [ ] Beta testing (100+ users)
- [ ] PyPI packaging
- [ ] Public launch

---

## Performance Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| Single file | <100ms | Efficient AST parsing |
| 100 files | <5s | Sequential (MVP), parallel (v1.1) |
| Memory | <200MB | Process files one at a time |

---

## Key Design Patterns

### 1. Rule Pattern
```python
class MyRule(BaseRule, ast.NodeVisitor):
    rule_id = "DL999"
    rule_name = "my-rule"

    def analyze(self, context: RuleContext) -> List[Violation]:
        self.visit(context.ast_tree)
        return self.violations

    def visit_SomeNode(self, node):
        # Detection logic
        pass
```

### 2. Configuration
```yaml
# .daglinter.yml
rules:
  heavy-imports:
    enabled: true
    severity: error
    libraries: [pandas, numpy]
```

### 3. Output Formats
- **Terminal**: Rich-formatted, color-coded
- **JSON**: Machine-readable for CI/CD
- **SARIF**: GitHub Code Scanning integration

---

## Critical Success Factors

1. **Performance**: <100ms per file (enables interactive use)
2. **Accuracy**: <5% false positive rate (builds trust)
3. **Usability**: Works out-of-box, clear error messages
4. **Extensibility**: Plugin architecture for custom rules

---

## Quick Start for Developers

```bash
# Setup
git clone <repo>
cd daglinter
pip install -e ".[dev]"

# Run tests
pytest

# Run linter on itself
daglinter daglinter/

# Build package
python -m build
```

---

## Common Patterns

### AST Parsing
```python
tree = ast.parse(source_code)
# Walk tree with visitor pattern
```

### Scope Tracking
```python
# Track if code is at module level or inside function
scope_depth = 0  # Module level
scope_depth > 0  # Inside function/class
```

### Violation Creation
```python
violation = self.create_violation(
    context=context,
    node=ast_node,
    message="Description",
    suggestion="How to fix"
)
```

---

## Testing Strategy

### Test Coverage Targets
- Overall: ≥85%
- Rules: 100% (critical path)
- Formatters: ≥90%
- Utils: ≥80%

### Test Types
1. **Unit**: Test individual rules with code snippets
2. **Integration**: Test CLI end-to-end
3. **Performance**: Benchmark parsing speed
4. **Cross-platform**: Linux, macOS, Windows

---

## Extensibility Points

### Future Enhancements
1. **Custom rules**: Plugin system via entry points
2. **Custom formatters**: Register new output formats
3. **Auto-fix**: Safe code transformations
4. **IDE integration**: Language Server Protocol

---

## Go-to-Market Checklist

- [ ] 100+ beta users tested
- [ ] NPS ≥30
- [ ] False positive rate <10%
- [ ] All P0 bugs resolved
- [ ] Documentation complete
- [ ] Performance targets met
- [ ] 3+ case studies
- [ ] CI/CD tested on 2+ platforms

---

## Support Resources

- **Architecture Questions**: See [TECHNICAL_ARCHITECTURE.md](./TECHNICAL_ARCHITECTURE.md)
- **Requirements**: See [REQUIREMENTS.md](./REQUIREMENTS.md)
- **Sprint Planning**: See [USER_STORIES_BACKLOG.md](./USER_STORIES_BACKLOG.md)
- **Metrics**: See [SUCCESS_METRICS.md](./SUCCESS_METRICS.md)

---

## Contact

- **Product Owner**: [Name]
- **Engineering Lead**: [Name]
- **Tech Lead**: [Name]

---

**Last Updated**: 2025-11-13
**Version**: 1.0
