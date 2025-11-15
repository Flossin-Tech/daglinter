# Creating Custom Rules

Guide to creating custom linting rules for DAGLinter.

## Table of Contents

- [Overview](#overview)
- [Rule Anatomy](#rule-anatomy)
- [Step-by-Step Guide](#step-by-step-guide)
- [AST Visitor Pattern](#ast-visitor-pattern)
- [Testing Your Rule](#testing-your-rule)
- [Best Practices](#best-practices)
- [Examples](#examples)

## Overview

DAGLinter rules are Python classes that analyze Abstract Syntax Trees (ASTs) to detect anti-patterns in Airflow DAG files. Each rule inherits from `BaseRule` and implements the `analyze()` method.

### Rule Structure

```
src/daglinter/rules/
├── base.py              # BaseRule class
├── __init__.py          # Rule registration
├── heavy_imports.py     # DL001
├── database_calls.py    # DL002
├── missing_docs.py      # DL003
├── complex_deps.py      # DL004
└── your_new_rule.py     # Your custom rule
```

## Rule Anatomy

### Basic Rule Template

```python
import ast
from typing import List
from .base import BaseRule, Severity
from ..core.models import RuleContext, Violation

class YourCustomRule(BaseRule, ast.NodeVisitor):
    """
    Detect [describe what your rule detects].

    This rule checks for [detailed description].
    """

    rule_id = "DL005"  # Unique rule ID
    rule_name = "your-custom-rule"  # Kebab-case name
    default_severity = Severity.WARNING  # ERROR, WARNING, or INFO

    def __init__(self, config=None):
        """Initialize rule with optional configuration."""
        super().__init__(config)
        self.violations: List[Violation] = []
        self.context: RuleContext = None

        # Rule-specific configuration
        self.threshold = self.config.get('threshold', 10)

    def analyze(self, context: RuleContext) -> List[Violation]:
        """
        Analyze AST and return violations.

        Args:
            context: Analysis context with AST and metadata

        Returns:
            List of violations found
        """
        self.violations = []
        self.context = context

        # Visit all nodes in the AST
        self.visit(context.ast_tree)

        return self.violations

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """
        Called for every function definition.

        Override visit_* methods for node types you care about.
        """
        # Your detection logic here
        if self._is_violation(node):
            violation = self.create_violation(
                context=self.context,
                node=node,
                message="Description of the violation",
                suggestion="How to fix it"
            )
            self.violations.append(violation)

        # Continue visiting child nodes
        self.generic_visit(node)

    def _is_violation(self, node: ast.FunctionDef) -> bool:
        """Helper method to check if node violates rule."""
        # Your logic here
        return False
```

### Key Components

1. **Class Attributes**
   - `rule_id`: Unique identifier (e.g., "DL005")
   - `rule_name`: Human-readable name (e.g., "your-rule-name")
   - `default_severity`: Default severity level

2. **`__init__` Method**
   - Initialize parent class
   - Set up instance variables
   - Load rule-specific configuration

3. **`analyze` Method**
   - Required method that returns violations
   - Sets up context and visits AST

4. **`visit_*` Methods**
   - Override for AST node types you want to check
   - Follow naming pattern: `visit_NodeType`

## Step-by-Step Guide

### Step 1: Plan Your Rule

Before coding, define:

1. **What to detect**: Specific anti-pattern or issue
2. **Why it matters**: Impact on performance, maintainability, etc.
3. **How to detect**: Which AST nodes to inspect
4. **How to fix**: Suggestions for users

Example: "Detect tasks without timeout configured"
- **What**: Tasks missing timeout parameter
- **Why**: Tasks may hang indefinitely
- **How**: Check task decorator calls for timeout param
- **Fix**: Add timeout=timedelta(hours=2)

### Step 2: Create Rule File

```bash
# Create rule file
touch src/daglinter/rules/missing_timeout.py
```

### Step 3: Implement Rule Class

```python
# src/daglinter/rules/missing_timeout.py

import ast
from typing import List
from .base import BaseRule, Severity
from ..core.models import RuleContext, Violation

class MissingTimeoutRule(BaseRule, ast.NodeVisitor):
    """
    Detect tasks without timeout configuration.

    Tasks without timeouts may hang indefinitely, affecting
    DAG execution and resource utilization.
    """

    rule_id = "DL005"
    rule_name = "missing-timeout"
    default_severity = Severity.WARNING

    def __init__(self, config=None):
        super().__init__(config)
        self.violations: List[Violation] = []
        self.context: RuleContext = None

        # Configuration
        self.require_timeout = self.config.get('require_timeout', True)

    def analyze(self, context: RuleContext) -> List[Violation]:
        """Analyze tasks for missing timeouts."""
        self.violations = []
        self.context = context
        self.visit(context.ast_tree)
        return self.violations

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check task decorator for timeout parameter."""
        # Check if function has @task decorator
        for decorator in node.decorator_list:
            if self._is_task_decorator(decorator):
                if not self._has_timeout(decorator):
                    self._create_timeout_violation(node)

        self.generic_visit(node)

    def _is_task_decorator(self, decorator) -> bool:
        """Check if decorator is @task."""
        if isinstance(decorator, ast.Name):
            return decorator.id == 'task'
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id == 'task'
        return False

    def _has_timeout(self, decorator) -> bool:
        """Check if decorator call has timeout parameter."""
        if isinstance(decorator, ast.Call):
            for keyword in decorator.keywords:
                if keyword.arg == 'execution_timeout':
                    return True
        return False

    def _create_timeout_violation(self, node: ast.FunctionDef) -> None:
        """Create violation for missing timeout."""
        violation = self.create_violation(
            context=self.context,
            node=node,
            message=f"Task '{node.name}' missing timeout configuration",
            suggestion=(
                "Add execution_timeout parameter to @task decorator. "
                "Example: @task(execution_timeout=timedelta(hours=2))"
            )
        )
        self.violations.append(violation)
```

### Step 4: Register Rule

Add to `src/daglinter/rules/__init__.py`:

```python
from .base import BaseRule
from .heavy_imports import HeavyImportRule
from .database_calls import DatabaseConnectionRule
from .missing_docs import MissingDocsRule
from .complex_deps import ComplexDependencyRule
from .missing_timeout import MissingTimeoutRule  # Add this

__all__ = [
    'BaseRule',
    'HeavyImportRule',
    'DatabaseConnectionRule',
    'MissingDocsRule',
    'ComplexDependencyRule',
    'MissingTimeoutRule',  # Add this
]
```

### Step 5: Create Tests

```python
# tests/unit/rules/test_missing_timeout.py

import ast
import pytest
from pathlib import Path
from daglinter.rules.missing_timeout import MissingTimeoutRule
from daglinter.core.models import RuleContext, Severity

class TestMissingTimeoutRule:
    """Tests for missing timeout rule."""

    def test_task_without_timeout_fails(self):
        """Task without timeout should create violation."""
        code = """
from airflow.decorators import task

@task
def my_task():
    return "result"
"""
        violations = self._run_rule(code)

        assert len(violations) == 1
        assert violations[0].rule_id == "DL005"
        assert "timeout" in violations[0].message.lower()

    def test_task_with_timeout_passes(self):
        """Task with timeout should not create violation."""
        code = """
from airflow.decorators import task
from datetime import timedelta

@task(execution_timeout=timedelta(hours=2))
def my_task():
    return "result"
"""
        violations = self._run_rule(code)
        assert len(violations) == 0

    def test_regular_function_ignored(self):
        """Regular functions without @task should be ignored."""
        code = """
def my_function():
    return "result"
"""
        violations = self._run_rule(code)
        assert len(violations) == 0

    def _run_rule(self, code: str):
        """Helper to run rule on code."""
        tree = ast.parse(code)
        context = RuleContext(
            file_path=Path("test.py"),
            ast_tree=tree,
            source_code=code,
            source_lines=code.split('\n'),
            config={}
        )
        rule = MissingTimeoutRule()
        return rule.analyze(context)
```

### Step 6: Document Your Rule

Add documentation to `docs/user-guide/rules.md`.

### Step 7: Test and Submit

```bash
# Run tests
pytest tests/unit/rules/test_missing_timeout.py -v

# Check coverage
pytest --cov=daglinter.rules.missing_timeout

# Run on sample DAGs
daglinter examples/sample_dags/

# Submit PR
git add .
git commit -m "feat: add DL005 missing timeout rule"
git push origin feature/missing-timeout-rule
```

## AST Visitor Pattern

### Understanding the Pattern

The visitor pattern traverses the AST and calls methods for each node type:

```python
class MyRule(ast.NodeVisitor):
    def visit_FunctionDef(self, node):
        """Called for every function definition."""
        print(f"Found function: {node.name}")
        self.generic_visit(node)  # Visit children

    def visit_Call(self, node):
        """Called for every function call."""
        print("Found function call")
        self.generic_visit(node)
```

### Common Node Types

| Node Type | Represents | Use Case |
|-----------|------------|----------|
| `Module` | Entire file | File-level checks |
| `Import` | `import x` | Import checks |
| `ImportFrom` | `from x import y` | Import checks |
| `FunctionDef` | `def func():` | Function checks |
| `AsyncFunctionDef` | `async def func():` | Async function checks |
| `ClassDef` | `class X:` | Class checks |
| `Call` | `func()` | Function call checks |
| `Assign` | `x = y` | Assignment checks |
| `With` | `with x:` | Context manager checks |
| `For` | `for x in y:` | Loop checks |

### Visiting Examples

#### Check All Imports

```python
def visit_Import(self, node: ast.Import) -> None:
    """Check 'import X' statements."""
    for alias in node.names:
        module_name = alias.name
        print(f"Import: {module_name}")

    self.generic_visit(node)

def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
    """Check 'from X import Y' statements."""
    module = node.module
    names = [alias.name for alias in node.names]
    print(f"From {module} import {names}")

    self.generic_visit(node)
```

#### Check Function Calls

```python
def visit_Call(self, node: ast.Call) -> None:
    """Check all function calls."""
    func_name = self._get_call_name(node)
    print(f"Call to: {func_name}")

    self.generic_visit(node)

def _get_call_name(self, node: ast.Call) -> str:
    """Extract function name from Call node."""
    if isinstance(node.func, ast.Name):
        return node.func.id
    elif isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""
```

#### Track Scope

```python
class MyRule(BaseRule, ast.NodeVisitor):
    def __init__(self, config=None):
        super().__init__(config)
        self.scope_depth = 0

    def visit_FunctionDef(self, node):
        """Track entry into function."""
        self.scope_depth += 1
        print(f"Enter function (depth {self.scope_depth})")

        self.generic_visit(node)

        self.scope_depth -= 1
        print(f"Exit function (depth {self.scope_depth})")

    @property
    def is_module_level(self) -> bool:
        """Check if currently at module level."""
        return self.scope_depth == 0
```

## Best Practices

### 1. Clear Violation Messages

```python
# Good - specific and actionable
message = "Task 'process_data' missing execution_timeout parameter"
suggestion = "Add execution_timeout=timedelta(hours=2) to @task decorator"

# Bad - vague
message = "Task has problem"
suggestion = "Fix it"
```

### 2. Configurable Rules

```python
class MyRule(BaseRule):
    def __init__(self, config=None):
        super().__init__(config)

        # Allow configuration
        self.max_length = self.config.get('max_length', 100)
        self.require_docs = self.config.get('require_docs', True)
        self.custom_patterns = self.config.get('patterns', [])
```

### 3. Handle Edge Cases

```python
def visit_Call(self, node: ast.Call) -> None:
    """Handle edge cases in function calls."""
    # Check node structure exists
    if not node.func:
        return

    # Handle different call types
    if isinstance(node.func, ast.Name):
        func_name = node.func.id
    elif isinstance(node.func, ast.Attribute):
        func_name = node.func.attr
    else:
        # Unknown call type, skip
        return

    self.generic_visit(node)
```

### 4. Efficient Checking

```python
# Good - fail fast
def _should_check(self, node):
    """Quick pre-check before expensive analysis."""
    if not self.enabled:
        return False
    if not node.decorator_list:
        return False
    return True

def visit_FunctionDef(self, node):
    if not self._should_check(node):
        return

    # Do expensive check
    result = self._expensive_analysis(node)
```

### 5. Comprehensive Tests

```python
class TestMyRule:
    """Test all scenarios."""

    def test_positive_case(self):
        """Test when violation should be found."""
        pass

    def test_negative_case(self):
        """Test when no violation should be found."""
        pass

    def test_edge_case_empty(self):
        """Test empty input."""
        pass

    def test_edge_case_syntax_error(self):
        """Test invalid syntax."""
        pass

    def test_configuration(self):
        """Test rule configuration."""
        pass

    def test_disabled_rule(self):
        """Test disabled rule."""
        pass
```

## Examples

### Example 1: Check for SQL Injection Risk

```python
class SQLInjectionRule(BaseRule, ast.NodeVisitor):
    """Detect potential SQL injection in queries."""

    rule_id = "DL006"
    rule_name = "sql-injection-risk"
    default_severity = Severity.ERROR

    def visit_Call(self, node: ast.Call) -> None:
        """Check SQL execution calls."""
        if self._is_sql_execute(node):
            if self._has_string_formatting(node):
                violation = self.create_violation(
                    context=self.context,
                    node=node,
                    message="Potential SQL injection via string formatting",
                    suggestion="Use parameterized queries instead"
                )
                self.violations.append(violation)

        self.generic_visit(node)

    def _is_sql_execute(self, node: ast.Call) -> bool:
        """Check if call is SQL execute."""
        if isinstance(node.func, ast.Attribute):
            return node.func.attr in ('execute', 'executemany')
        return False

    def _has_string_formatting(self, node: ast.Call) -> bool:
        """Check if arguments use string formatting."""
        for arg in node.args:
            if isinstance(arg, (ast.JoinedStr, ast.FormattedValue)):
                return True  # f-string
            if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Mod):
                return True  # % formatting
        return False
```

### Example 2: Check Task Documentation

```python
class TaskDocsRule(BaseRule, ast.NodeVisitor):
    """Ensure tasks have documentation."""

    rule_id = "DL007"
    rule_name = "task-docs"
    default_severity = Severity.WARNING

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check task functions for docstrings."""
        if self._is_task(node):
            if not ast.get_docstring(node):
                violation = self.create_violation(
                    context=self.context,
                    node=node,
                    message=f"Task '{node.name}' missing docstring",
                    suggestion="Add docstring explaining task purpose"
                )
                self.violations.append(violation)

        self.generic_visit(node)

    def _is_task(self, node: ast.FunctionDef) -> bool:
        """Check if function is decorated with @task."""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id == 'task':
                    return True
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    if decorator.func.id == 'task':
                        return True
        return False
```

## See Also

- [Testing Guide](testing.md) - How to test your rule
- [Architecture](architecture.md) - System architecture
- [Contributing Guide](contributing.md) - Contribution process
- [Development Setup](development-setup.md) - Development environment
