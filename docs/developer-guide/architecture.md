# DAGLinter - Technical Architecture Specification

## Document Overview

**Version:** 1.0
**Date:** 2025-11-13
**Status:** Design Document
**Target Audience:** Engineering team implementing MVP

This document provides the detailed technical architecture for DAGLinter, a static analysis tool for Apache Airflow DAG files. It translates requirements into concrete implementation specifications.

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Technology Stack](#2-technology-stack)
3. [Core Components Design](#3-core-components-design)
4. [Rule Implementation Pattern](#4-rule-implementation-pattern)
5. [MVP Rules Implementation Specs](#5-mvp-rules-implementation-specs)
6. [File Structure](#6-file-structure)
7. [Performance Architecture](#7-performance-architecture)
8. [Extensibility Architecture](#8-extensibility-architecture)
9. [Integration Points](#9-integration-points)
10. [Data Flow](#10-data-flow)
11. [Error Handling Strategy](#11-error-handling-strategy)
12. [Testing Architecture](#12-testing-architecture)

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Entry Point                          │
│                      (daglinter/__main__.py)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Argument Parser                             │
│                    (cli/argument_parser.py)                      │
│  • Parse CLI arguments                                           │
│  • Load configuration files                                      │
│  • Merge config with CLI overrides                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      File Discovery                              │
│                    (core/file_scanner.py)                        │
│  • Scan directories recursively                                  │
│  • Filter Python files                                           │
│  • Apply exclude patterns                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Linting Orchestrator                        │
│                    (core/linter.py)                              │
│  • Coordinate parsing and rule execution                         │
│  • Manage rule registry                                          │
│  • Collect violations                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│     AST Parser Module    │    │     Rule Engine          │
│  (core/ast_parser.py)    │    │  (rules/base_rule.py)    │
│                          │    │  (rules/registry.py)     │
│  • Parse Python files    │    │                          │
│  • Build AST             │    │  • Rule registration     │
│  • Handle syntax errors  │    │  • Rule execution        │
│  • Extract metadata      │    │  • Context management    │
└──────────────────────────┘    └──────────────┬───────────┘
                                               │
                                               ▼
                        ┌─────────────────────────────────────┐
                        │         Specific Rules              │
                        ├─────────────────────────────────────┤
                        │  • HeavyImportRule                  │
                        │  • DatabaseConnectionRule           │
                        │  • MissingDocsRule                  │
                        │  • ComplexDependencyRule            │
                        └──────────────┬──────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Violation Collector                           │
│                    (core/violations.py)                          │
│  • Aggregate violations                                          │
│  • Sort and deduplicate                                          │
│  • Calculate statistics                                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Reporter/Formatter                            │
│                    (formatters/base.py)                          │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Terminal   │  │     JSON     │  │    SARIF     │          │
│  │   Reporter   │  │   Formatter  │  │  Formatter   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                        Exit Code
```

### 1.2 Component Responsibilities

| Component | Responsibility | Key Classes |
|-----------|----------------|-------------|
| **CLI Entry Point** | Parse arguments, orchestrate execution | `main()`, `CLIApplication` |
| **Configuration Manager** | Load and merge configurations | `ConfigLoader`, `Config` |
| **File Scanner** | Discover Python files to analyze | `FileScanner` |
| **AST Parser** | Parse Python to AST, handle errors | `ASTParser`, `ParseResult` |
| **Rule Engine** | Register, configure, execute rules | `RuleRegistry`, `RuleContext` |
| **Specific Rules** | Implement detection logic | `HeavyImportRule`, `DatabaseConnectionRule`, etc. |
| **Violation Collector** | Aggregate and process violations | `ViolationCollector`, `Violation` |
| **Formatters** | Output violations in various formats | `TerminalFormatter`, `JSONFormatter`, `SARIFFormatter` |

---

## 2. Technology Stack

### 2.1 Core Dependencies

| Dependency | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **Python** | 3.8+ | Runtime | Match Airflow 2.x requirements |
| **ast** | stdlib | AST parsing | Native, no external deps, comprehensive |
| **pathlib** | stdlib | Path handling | Cross-platform, modern |
| **argparse** | stdlib | CLI argument parsing | Sufficient for MVP, stdlib |
| **pyyaml** | 6.0+ | Config file parsing | Industry standard for YAML |
| **rich** | 13.0+ | Terminal formatting | Best-in-class terminal UI library |
| **typing** | stdlib | Type hints | Code clarity, IDE support |

### 2.2 Development Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| **pytest** | 7.0+ | Testing framework |
| **pytest-cov** | 4.0+ | Coverage reporting |
| **black** | 23.0+ | Code formatting |
| **mypy** | 1.0+ | Type checking |
| **ruff** | 0.1+ | Fast linting |

### 2.3 Optional Dependencies (Post-MVP)

- **click**: Alternative CLI framework if argparse limitations hit
- **jsonschema**: Config file validation
- **toml**: pyproject.toml support

### 2.4 Rationale for Choices

**Why `ast` over tree-sitter or libCST?**
- Native to Python, zero installation friction
- Complete coverage of Python syntax
- Sufficient for static analysis needs
- Well-documented and stable

**Why `rich` over colorama?**
- Superior formatting capabilities
- Built-in progress bars, tables, syntax highlighting
- Active maintenance, excellent docs
- Handles NO_COLOR automatically

**Why `argparse` over click?**
- Standard library, zero deps
- Sufficient for MVP CLI needs
- Can migrate to click later if needed

---

## 3. Core Components Design

### 3.1 AST Parser Module

**File:** `daglinter/core/ast_parser.py`

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import ast

@dataclass
class ParseResult:
    """Result of parsing a Python file."""
    file_path: Path
    ast_tree: Optional[ast.AST]
    success: bool
    error: Optional[str] = None
    parse_time_ms: float = 0.0

class ASTParser:
    """Parses Python files into AST for analysis."""

    def parse_file(self, file_path: Path) -> ParseResult:
        """
        Parse a Python file into an AST.

        Args:
            file_path: Path to Python file

        Returns:
            ParseResult with AST or error information
        """
        start_time = time.perf_counter()

        try:
            source_code = file_path.read_text(encoding='utf-8')
            tree = ast.parse(source_code, filename=str(file_path))

            parse_time = (time.perf_counter() - start_time) * 1000

            return ParseResult(
                file_path=file_path,
                ast_tree=tree,
                success=True,
                parse_time_ms=parse_time
            )

        except SyntaxError as e:
            return ParseResult(
                file_path=file_path,
                ast_tree=None,
                success=False,
                error=f"Syntax error at line {e.lineno}: {e.msg}"
            )
        except Exception as e:
            return ParseResult(
                file_path=file_path,
                ast_tree=None,
                success=False,
                error=f"Parse error: {str(e)}"
            )
```

**Design Decisions:**
- Graceful error handling prevents one bad file from crashing entire scan
- Performance tracking built-in for optimization
- Returns dataclass for type safety and clarity
- Handles encoding issues with explicit UTF-8

---

### 3.2 Rule Engine

**File:** `daglinter/rules/base_rule.py`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional
import ast

class Severity(Enum):
    """Severity levels for violations."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class Violation:
    """Represents a single linting violation."""
    rule_id: str
    rule_name: str
    severity: Severity
    file_path: Path
    line: int
    column: int
    message: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None

@dataclass
class RuleContext:
    """Context provided to rules during analysis."""
    file_path: Path
    ast_tree: ast.AST
    source_code: str
    config: dict  # Rule-specific configuration

class BaseRule(ABC):
    """Base class for all linting rules."""

    # Class attributes - override in subclasses
    rule_id: str = "DL000"
    rule_name: str = "base-rule"
    default_severity: Severity = Severity.ERROR

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize rule with optional configuration.

        Args:
            config: Rule-specific configuration
        """
        self.config = config or {}
        self.severity = Severity(
            self.config.get('severity', self.default_severity.value)
        )
        self.enabled = self.config.get('enabled', True)

    @abstractmethod
    def analyze(self, context: RuleContext) -> List[Violation]:
        """
        Analyze AST and return violations.

        Args:
            context: Analysis context with AST and metadata

        Returns:
            List of violations found
        """
        pass

    def create_violation(
        self,
        context: RuleContext,
        node: ast.AST,
        message: str,
        suggestion: Optional[str] = None
    ) -> Violation:
        """
        Helper to create a violation from an AST node.

        Args:
            context: Analysis context
            node: AST node where violation occurred
            message: Description of the violation
            suggestion: Optional fix suggestion

        Returns:
            Violation object
        """
        return Violation(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            severity=self.severity,
            file_path=context.file_path,
            line=node.lineno,
            column=node.col_offset,
            message=message,
            suggestion=suggestion,
            code_snippet=self._extract_code_snippet(context, node)
        )

    def _extract_code_snippet(
        self,
        context: RuleContext,
        node: ast.AST
    ) -> Optional[str]:
        """Extract source code for the violating line."""
        try:
            lines = context.source_code.split('\n')
            if 0 < node.lineno <= len(lines):
                return lines[node.lineno - 1].strip()
        except Exception:
            pass
        return None
```

**File:** `daglinter/rules/registry.py`

```python
from typing import Dict, List, Type
from .base_rule import BaseRule

class RuleRegistry:
    """Central registry for all linting rules."""

    def __init__(self):
        self._rules: Dict[str, Type[BaseRule]] = {}

    def register(self, rule_class: Type[BaseRule]) -> None:
        """
        Register a rule class.

        Args:
            rule_class: Rule class to register
        """
        self._rules[rule_class.rule_id] = rule_class

    def get_enabled_rules(self, config: dict) -> List[BaseRule]:
        """
        Get instances of enabled rules based on config.

        Args:
            config: Configuration dictionary

        Returns:
            List of instantiated, enabled rules
        """
        rules = []
        rule_configs = config.get('rules', {})

        for rule_id, rule_class in self._rules.items():
            rule_config = rule_configs.get(
                rule_class.rule_name,
                {'enabled': True}
            )

            rule_instance = rule_class(config=rule_config)

            if rule_instance.enabled:
                rules.append(rule_instance)

        return rules

# Global registry instance
registry = RuleRegistry()
```

---

### 3.3 Configuration Manager

**File:** `daglinter/core/config.py`

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import yaml

@dataclass
class Config:
    """Application configuration."""

    # Rule configurations
    rules: Dict[str, dict] = field(default_factory=dict)

    # File/directory exclusions
    exclude: List[str] = field(default_factory=list)

    # File/directory inclusions
    include: List[str] = field(default_factory=list)

    # Output settings
    output_format: str = "text"
    output_file: Optional[Path] = None
    color: str = "auto"  # auto, always, never
    verbose: bool = False
    quiet: bool = False

    # Performance settings
    max_workers: int = 1  # Single-threaded for MVP
    timeout_per_file: int = 30

    @classmethod
    def from_file(cls, config_path: Path) -> 'Config':
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to .daglinter.yml

        Returns:
            Config instance
        """
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f) or {}

        return cls(
            rules=data.get('rules', {}),
            exclude=data.get('exclude', []),
            include=data.get('include', []),
            output_format=data.get('output', {}).get('format', 'text'),
            color=data.get('output', {}).get('color', 'auto'),
            verbose=data.get('output', {}).get('verbose', False),
            max_workers=data.get('performance', {}).get('max_workers', 1),
            timeout_per_file=data.get('performance', {}).get('timeout_per_file', 30)
        )

    @classmethod
    def default(cls) -> 'Config':
        """Create default configuration."""
        return cls(
            exclude=['**/tests/**', '**/__pycache__/**', '*.pyc'],
            rules={
                'heavy-imports': {
                    'enabled': True,
                    'severity': 'error',
                    'libraries': [
                        'pandas', 'numpy', 'sklearn', 'tensorflow',
                        'torch', 'matplotlib', 'seaborn', 'plotly'
                    ]
                },
                'db-connections': {
                    'enabled': True,
                    'severity': 'error'
                },
                'missing-docs': {
                    'enabled': True,
                    'severity': 'warning',
                    'min_length': 20
                },
                'complex-dependencies': {
                    'enabled': True,
                    'severity': 'warning',
                    'max_fan_out': 10,
                    'max_fan_in': 10,
                    'max_depth': 5
                }
            }
        )

    def merge_cli_args(self, **kwargs) -> 'Config':
        """
        Merge CLI arguments into config (CLI takes precedence).

        Args:
            **kwargs: CLI arguments

        Returns:
            New Config with merged values
        """
        # Create a copy and override with CLI args
        config_dict = self.__dict__.copy()

        for key, value in kwargs.items():
            if value is not None:
                config_dict[key] = value

        return Config(**config_dict)

class ConfigLoader:
    """Discovers and loads configuration files."""

    CONFIG_FILENAMES = ['.daglinter.yml', '.daglinter.yaml']

    @staticmethod
    def discover_config(start_path: Path) -> Optional[Path]:
        """
        Search for config file from start_path up to root.

        Args:
            start_path: Directory to start search

        Returns:
            Path to config file or None
        """
        current = start_path.resolve()

        while True:
            for filename in ConfigLoader.CONFIG_FILENAMES:
                config_path = current / filename
                if config_path.exists():
                    return config_path

            # Move up one directory
            parent = current.parent
            if parent == current:  # Reached root
                break
            current = parent

        return None

    @staticmethod
    def load(config_path: Optional[Path] = None) -> Config:
        """
        Load configuration, with fallback to defaults.

        Args:
            config_path: Explicit config path or None to discover

        Returns:
            Config instance
        """
        if config_path and config_path.exists():
            return Config.from_file(config_path)

        # Auto-discover
        discovered = ConfigLoader.discover_config(Path.cwd())
        if discovered:
            return Config.from_file(discovered)

        # Fall back to defaults
        return Config.default()
```

---

### 3.4 Violation Reporter

**File:** `daglinter/formatters/terminal.py`

```python
from typing import List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from ..core.violations import Violation, Severity

class TerminalFormatter:
    """Formats violations for terminal output using Rich."""

    def __init__(self, color: str = "auto"):
        """
        Initialize terminal formatter.

        Args:
            color: Color mode (auto, always, never)
        """
        self.console = Console(
            force_terminal=(color == "always"),
            no_color=(color == "never")
        )

    def format_violations(
        self,
        violations: List[Violation],
        files_scanned: int
    ) -> None:
        """
        Format and print violations to terminal.

        Args:
            violations: List of violations to display
            files_scanned: Total number of files scanned
        """
        if not violations:
            self._print_success(files_scanned)
            return

        # Group violations by file
        by_file = {}
        for v in violations:
            if v.file_path not in by_file:
                by_file[v.file_path] = []
            by_file[v.file_path].append(v)

        # Print violations per file
        self.console.print("\n[bold]Scanning DAGs...[/bold]")
        self.console.rule()

        for file_path, file_violations in by_file.items():
            self.console.print(f"\n[bold]{file_path}[/bold]")

            for violation in file_violations:
                self._print_violation(violation)

        self.console.rule()
        self._print_summary(violations, files_scanned)

    def _print_violation(self, violation: Violation) -> None:
        """Print a single violation."""
        # Color based on severity
        if violation.severity == Severity.ERROR:
            icon = "✗"
            color = "red"
        elif violation.severity == Severity.WARNING:
            icon = "⚠"
            color = "yellow"
        else:
            icon = "ℹ"
            color = "blue"

        # Main violation line
        self.console.print(
            f"  [{color}]{icon} {violation.rule_id} "
            f"{violation.severity.value.upper()} (line {violation.line}): "
            f"{violation.message}[/{color}]"
        )

        # Code snippet
        if violation.code_snippet:
            self.console.print(f"    → {violation.code_snippet}", style="dim")

        # Suggestion
        if violation.suggestion:
            self.console.print(
                f"\n    [italic]Suggestion: {violation.suggestion}[/italic]\n"
            )

    def _print_summary(
        self,
        violations: List[Violation],
        files_scanned: int
    ) -> None:
        """Print summary statistics."""
        errors = sum(1 for v in violations if v.severity == Severity.ERROR)
        warnings = sum(1 for v in violations if v.severity == Severity.WARNING)
        clean = files_scanned - len(set(v.file_path for v in violations))

        self.console.print("\n[bold]Summary:[/bold]")
        self.console.print(f"  Files scanned: {files_scanned}")
        if clean > 0:
            self.console.print(f"  ✓ Clean files: {clean}", style="green")
        if errors > 0:
            self.console.print(f"  ✗ Errors: {errors}", style="red")
        if warnings > 0:
            self.console.print(f"  ⚠ Warnings: {warnings}", style="yellow")

        if errors > 0:
            self.console.print(
                f"\n❌ Linting failed with {errors} error(s)",
                style="bold red"
            )
        elif warnings > 0:
            self.console.print(
                f"\n⚠ Linting passed with {warnings} warning(s)",
                style="bold yellow"
            )

    def _print_success(self, files_scanned: int) -> None:
        """Print success message when no violations found."""
        self.console.print(
            f"\n✓ All {files_scanned} files passed linting!",
            style="bold green"
        )
```

**File:** `daglinter/formatters/json_formatter.py`

```python
import json
from datetime import datetime
from pathlib import Path
from typing import List
from ..core.violations import Violation

class JSONFormatter:
    """Formats violations as JSON."""

    @staticmethod
    def format_violations(
        violations: List[Violation],
        files_scanned: int,
        version: str = "1.0.0"
    ) -> str:
        """
        Format violations as JSON.

        Args:
            violations: List of violations
            files_scanned: Number of files scanned
            version: Tool version

        Returns:
            JSON string
        """
        errors = sum(1 for v in violations if v.severity.value == "error")
        warnings = sum(1 for v in violations if v.severity.value == "warning")

        output = {
            "version": version,
            "scan_time": datetime.utcnow().isoformat() + "Z",
            "summary": {
                "files_scanned": files_scanned,
                "errors": errors,
                "warnings": warnings,
                "total_violations": len(violations)
            },
            "violations": [
                {
                    "file": str(v.file_path),
                    "line": v.line,
                    "column": v.column,
                    "severity": v.severity.value,
                    "rule_id": v.rule_id,
                    "rule_name": v.rule_name,
                    "message": v.message,
                    "suggestion": v.suggestion,
                    "code_snippet": v.code_snippet
                }
                for v in violations
            ]
        }

        return json.dumps(output, indent=2)
```

---

## 4. Rule Implementation Pattern

### 4.1 Base Pattern for All Rules

Every rule follows this pattern:

1. **Inherit from `BaseRule`**
2. **Define class attributes**: `rule_id`, `rule_name`, `default_severity`
3. **Implement `analyze()` method**: Use AST visitor pattern
4. **Return list of violations**

### 4.2 AST Visitor Pattern

Python's AST provides a `NodeVisitor` base class for traversing the tree. We'll use this pattern:

```python
import ast
from typing import List
from .base_rule import BaseRule, RuleContext, Violation

class ExampleRule(BaseRule, ast.NodeVisitor):
    """Example rule implementation."""

    rule_id = "DL999"
    rule_name = "example-rule"

    def __init__(self, config=None):
        super().__init__(config)
        self.violations: List[Violation] = []
        self.context: Optional[RuleContext] = None

    def analyze(self, context: RuleContext) -> List[Violation]:
        """Analyze AST and return violations."""
        self.violations = []
        self.context = context

        # Visit all nodes in the AST
        self.visit(context.ast_tree)

        return self.violations

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Called for every function definition."""
        # Your logic here
        # Use self.create_violation() to record issues

        # Continue visiting child nodes
        self.generic_visit(node)
```

### 4.3 Scope Analysis Helper

Many rules need to know if code is at module level or inside a function/class:

```python
class ScopeTracker(ast.NodeVisitor):
    """Helper to track scope during AST traversal."""

    def __init__(self):
        self.scope_stack: List[ast.AST] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.scope_stack.append(node)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.scope_stack.append(node)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scope_stack.append(node)
        self.generic_visit(node)
        self.scope_stack.pop()

    @property
    def is_module_level(self) -> bool:
        """Check if currently at module level."""
        return len(self.scope_stack) == 0

    @property
    def is_inside_function(self) -> bool:
        """Check if inside a function."""
        return any(
            isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef))
            for scope in self.scope_stack
        )
```

---

## 5. MVP Rules Implementation Specs

### 5.1 Rule 1: Heavy Import Detection (DL001)

**File:** `daglinter/rules/heavy_imports.py`

```python
import ast
from typing import List, Set
from .base_rule import BaseRule, RuleContext, Violation, Severity

class HeavyImportRule(BaseRule, ast.NodeVisitor):
    """Detect heavy libraries imported at module level."""

    rule_id = "DL001"
    rule_name = "heavy-imports"
    default_severity = Severity.ERROR

    DEFAULT_HEAVY_LIBRARIES = {
        'pandas', 'numpy', 'sklearn', 'tensorflow', 'torch',
        'matplotlib', 'seaborn', 'plotly', 'scipy', 'cv2',
        'PIL', 'keras', 'xgboost', 'lightgbm'
    }

    def __init__(self, config=None):
        super().__init__(config)
        self.violations: List[Violation] = []
        self.context: RuleContext = None
        self.scope_depth = 0

        # Get configured heavy libraries
        custom_libs = self.config.get('libraries', [])
        self.heavy_libraries = (
            self.DEFAULT_HEAVY_LIBRARIES | set(custom_libs)
        )

    def analyze(self, context: RuleContext) -> List[Violation]:
        """Analyze imports in the AST."""
        self.violations = []
        self.context = context
        self.scope_depth = 0

        self.visit(context.ast_tree)

        return self.violations

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track entry into function scope."""
        self.scope_depth += 1
        self.generic_visit(node)
        self.scope_depth -= 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Track entry into async function scope."""
        self.scope_depth += 1
        self.generic_visit(node)
        self.scope_depth -= 1

    def visit_Import(self, node: ast.Import) -> None:
        """Check 'import X' statements."""
        if self.scope_depth == 0:  # Module level
            for alias in node.names:
                base_module = alias.name.split('.')[0]
                if base_module in self.heavy_libraries:
                    self._create_import_violation(node, alias.name)

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check 'from X import Y' statements."""
        if self.scope_depth == 0 and node.module:  # Module level
            base_module = node.module.split('.')[0]
            if base_module in self.heavy_libraries:
                self._create_import_violation(node, node.module)

        self.generic_visit(node)

    def _create_import_violation(self, node: ast.AST, module_name: str) -> None:
        """Create a violation for a heavy import."""
        violation = self.create_violation(
            context=self.context,
            node=node,
            message=f"Heavy import '{module_name}' at module level",
            suggestion=(
                f"Move 'import {module_name}' inside your task function "
                "to avoid slowing DAG parsing"
            )
        )
        self.violations.append(violation)
```

**How it works:**
1. Tracks scope depth (0 = module level, >0 = inside function/class)
2. Visits all `Import` and `ImportFrom` nodes
3. Checks if the base module is in the heavy libraries set
4. Creates violation only if at module level (scope_depth == 0)

**Test cases to cover:**
- `import pandas` at module level → FAIL
- `import pandas` inside function → PASS
- `from numpy import array` at module level → FAIL
- `from numpy import array` inside @task function → PASS
- Custom library in config → FAIL at module level
- Non-heavy library → PASS

---

### 5.2 Rule 2: Database Connection Detection (DL002)

**File:** `daglinter/rules/db_connections.py`

```python
import ast
from typing import List, Set, Tuple
from .base_rule import BaseRule, RuleContext, Violation, Severity

class DatabaseConnectionRule(BaseRule, ast.NodeVisitor):
    """Detect database connections outside task context."""

    rule_id = "DL002"
    rule_name = "db-connections"
    default_severity = Severity.ERROR

    # Patterns: (module, function_name)
    DB_CONNECTION_PATTERNS = [
        ('psycopg2', 'connect'),
        ('pymongo', 'MongoClient'),
        ('mysql.connector', 'connect'),
        ('sqlite3', 'connect'),
        ('sqlalchemy', 'create_engine'),
        ('pymssql', 'connect'),
        ('cx_Oracle', 'connect'),
    ]

    # Airflow hooks are OK
    AIRFLOW_HOOK_MODULES = {
        'airflow.hooks',
        'airflow.providers',
    }

    def __init__(self, config=None):
        super().__init__(config)
        self.violations: List[Violation] = []
        self.context: RuleContext = None
        self.scope_depth = 0
        self.is_airflow_hook_context = False

    def analyze(self, context: RuleContext) -> List[Violation]:
        """Analyze database connections."""
        self.violations = []
        self.context = context
        self.scope_depth = 0

        self.visit(context.ast_tree)

        return self.violations

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track entry into function scope."""
        self.scope_depth += 1
        self.generic_visit(node)
        self.scope_depth -= 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Track entry into async function scope."""
        self.scope_depth += 1
        self.generic_visit(node)
        self.scope_depth -= 1

    def visit_Call(self, node: ast.Call) -> None:
        """Check function calls for DB connections."""
        if self.scope_depth == 0:  # Module level
            if self._is_db_connection(node):
                if not self._is_airflow_hook(node):
                    self._create_db_violation(node)

        self.generic_visit(node)

    def _is_db_connection(self, node: ast.Call) -> bool:
        """Check if call matches DB connection patterns."""
        # Get the function being called
        func_name = self._get_call_name(node)

        if not func_name:
            return False

        # Check against patterns
        for module, function in self.DB_CONNECTION_PATTERNS:
            if func_name.endswith(f"{module}.{function}"):
                return True
            if func_name == function and self._module_imported(module):
                return True

        return False

    def _is_airflow_hook(self, node: ast.Call) -> bool:
        """Check if call is to Airflow Hook."""
        func_name = self._get_call_name(node)

        if not func_name:
            return False

        for hook_module in self.AIRFLOW_HOOK_MODULES:
            if func_name.startswith(hook_module):
                return True

        return False

    def _get_call_name(self, node: ast.Call) -> str:
        """Extract full name of called function."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            # Build full path: obj.attr or module.func
            parts = []
            current = node.func

            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value

            if isinstance(current, ast.Name):
                parts.append(current.id)

            return '.'.join(reversed(parts))

        return ""

    def _module_imported(self, module: str) -> bool:
        """Check if module is imported (simplified check)."""
        # This is a simplified implementation
        # In production, track imports during traversal
        source = self.context.source_code
        return f"import {module}" in source or f"from {module}" in source

    def _create_db_violation(self, node: ast.Call) -> None:
        """Create violation for database connection."""
        func_name = self._get_call_name(node)

        violation = self.create_violation(
            context=self.context,
            node=node,
            message=f"Database connection '{func_name}' outside task context",
            suggestion=(
                "Use Airflow Hooks inside task functions instead. "
                "Example: PostgresHook(postgres_conn_id='...')"
            )
        )
        self.violations.append(violation)
```

**How it works:**
1. Tracks scope depth (module level vs inside functions)
2. Visits all function calls (`ast.Call` nodes)
3. Checks if call matches DB connection patterns
4. Excludes Airflow Hooks (valid pattern)
5. Creates violation only at module level

**Improvement for production:**
- Track imports to build accurate module resolution
- Handle `import X as Y` aliases
- Detect connection pooling patterns

---

### 5.3 Rule 3: Missing DAG Documentation (DL003)

**File:** `daglinter/rules/missing_docs.py`

```python
import ast
from typing import List, Optional
from .base_rule import BaseRule, RuleContext, Violation, Severity

class MissingDocsRule(BaseRule, ast.NodeVisitor):
    """Detect DAGs without documentation."""

    rule_id = "DL003"
    rule_name = "missing-docs"
    default_severity = Severity.WARNING

    def __init__(self, config=None):
        super().__init__(config)
        self.violations: List[Violation] = []
        self.context: RuleContext = None
        self.min_length = self.config.get('min_length', 20)

    def analyze(self, context: RuleContext) -> List[Violation]:
        """Analyze DAG documentation."""
        self.violations = []
        self.context = context

        self.visit(context.ast_tree)

        return self.violations

    def visit_Call(self, node: ast.Call) -> None:
        """Check DAG constructor calls."""
        if self._is_dag_constructor(node):
            doc_param = self._get_doc_parameter(node)

            if not doc_param or not self._is_valid_doc(doc_param):
                self._create_docs_violation(node)

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Check DAG assignments with context manager."""
        # Handle: dag = DAG(...)
        if isinstance(node.value, ast.Call):
            self.visit_Call(node.value)

        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        """Check DAG context managers."""
        # Handle: with DAG(...) as dag:
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                if self._is_dag_constructor(item.context_expr):
                    doc_param = self._get_doc_parameter(item.context_expr)

                    if not doc_param or not self._is_valid_doc(doc_param):
                        self._create_docs_violation(item.context_expr)

        self.generic_visit(node)

    def _is_dag_constructor(self, node: ast.Call) -> bool:
        """Check if call is DAG constructor."""
        # Check for: DAG(...)
        if isinstance(node.func, ast.Name) and node.func.id == 'DAG':
            return True

        # Check for: airflow.DAG(...)
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'DAG':
                return True

        return False

    def _get_doc_parameter(self, node: ast.Call) -> Optional[str]:
        """Extract doc_md or description parameter."""
        # Check keyword arguments
        for keyword in node.keywords:
            if keyword.arg in ('doc_md', 'description'):
                if isinstance(keyword.value, ast.Constant):
                    return keyword.value.value
                elif isinstance(keyword.value, ast.Str):  # Python 3.7 compat
                    return keyword.value.s

        return None

    def _is_valid_doc(self, doc: str) -> bool:
        """Check if documentation is meaningful."""
        if not doc or not isinstance(doc, str):
            return False

        doc_stripped = doc.strip()

        # Too short
        if len(doc_stripped) < self.min_length:
            return False

        # Placeholder text
        placeholders = ['todo', 'tbd', 'fixme', 'xxx', 'placeholder']
        if doc_stripped.lower() in placeholders:
            return False

        return True

    def _create_docs_violation(self, node: ast.Call) -> None:
        """Create violation for missing documentation."""
        violation = self.create_violation(
            context=self.context,
            node=node,
            message="DAG missing meaningful documentation",
            suggestion=(
                "Add doc_md parameter with DAG purpose, schedule, and owner. "
                f"Minimum length: {self.min_length} characters"
            )
        )
        self.violations.append(violation)
```

**How it works:**
1. Visits `Call`, `Assign`, and `With` nodes to find DAG constructors
2. Checks for `doc_md` or `description` parameters
3. Validates documentation is not empty, too short, or placeholder text
4. Creates warning-level violation if documentation insufficient

---

### 5.4 Rule 4: Complex Dependencies (DL004)

**File:** `daglinter/rules/complex_dependencies.py`

```python
import ast
from typing import List, Dict, Set
from collections import defaultdict
from .base_rule import BaseRule, RuleContext, Violation, Severity

class ComplexDependencyRule(BaseRule, ast.NodeVisitor):
    """Detect overly complex task dependency patterns."""

    rule_id = "DL004"
    rule_name = "complex-dependencies"
    default_severity = Severity.WARNING

    def __init__(self, config=None):
        super().__init__(config)
        self.violations: List[Violation] = []
        self.context: RuleContext = None

        # Configurable thresholds
        self.max_fan_out = self.config.get('max_fan_out', 10)
        self.max_fan_in = self.config.get('max_fan_in', 10)
        self.max_depth = self.config.get('max_depth', 5)

        # Dependency graph
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_deps: Dict[str, Set[str]] = defaultdict(set)

    def analyze(self, context: RuleContext) -> List[Violation]:
        """Analyze task dependencies."""
        self.violations = []
        self.context = context
        self.dependencies = defaultdict(set)
        self.reverse_deps = defaultdict(set)

        # Build dependency graph
        self.visit(context.ast_tree)

        # Check for complex patterns
        self._check_fan_out()
        self._check_fan_in()
        # max_depth check deferred to post-MVP (requires graph traversal)

        return self.violations

    def visit_BinOp(self, node: ast.BinOp) -> None:
        """Check >> and << operators for dependencies."""
        if isinstance(node.op, ast.RShift):  # >>
            self._add_dependency(node.left, node.right)
        elif isinstance(node.op, ast.LShift):  # <<
            self._add_dependency(node.right, node.left)

        self.generic_visit(node)

    def _add_dependency(self, upstream, downstream) -> None:
        """Add dependency to graph."""
        # Extract task names
        upstream_tasks = self._extract_task_names(upstream)
        downstream_tasks = self._extract_task_names(downstream)

        for up in upstream_tasks:
            for down in downstream_tasks:
                self.dependencies[up].add(down)
                self.reverse_deps[down].add(up)

    def _extract_task_names(self, node: ast.AST) -> List[str]:
        """Extract task names from AST node."""
        names = []

        if isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.List):
            for elt in node.elts:
                names.extend(self._extract_task_names(elt))
        elif isinstance(node, ast.Tuple):
            for elt in node.elts:
                names.extend(self._extract_task_names(elt))

        return names

    def _check_fan_out(self) -> None:
        """Check for excessive downstream dependencies."""
        for task, downstream in self.dependencies.items():
            if len(downstream) > self.max_fan_out:
                # Find the node for better error reporting
                # Simplified: create generic violation
                violation = Violation(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    severity=self.severity,
                    file_path=self.context.file_path,
                    line=0,  # Would need to track in production
                    column=0,
                    message=(
                        f"Task '{task}' has {len(downstream)} downstream "
                        f"dependencies (max: {self.max_fan_out})"
                    ),
                    suggestion=(
                        "Consider using TaskGroup to organize related tasks "
                        "or dynamic task mapping for better maintainability"
                    )
                )
                self.violations.append(violation)

    def _check_fan_in(self) -> None:
        """Check for excessive upstream dependencies."""
        for task, upstream in self.reverse_deps.items():
            if len(upstream) > self.max_fan_in:
                violation = Violation(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    severity=self.severity,
                    file_path=self.context.file_path,
                    line=0,
                    column=0,
                    message=(
                        f"Task '{task}' has {len(upstream)} upstream "
                        f"dependencies (max: {self.max_fan_in})"
                    ),
                    suggestion=(
                        "Consider refactoring to reduce coupling or "
                        "use intermediate aggregation tasks"
                    )
                )
                self.violations.append(violation)
```

**How it works:**
1. Visits `BinOp` nodes to find `>>` and `<<` operators
2. Builds dependency graph tracking upstream and downstream relationships
3. Counts fan-out (downstream) and fan-in (upstream) per task
4. Creates warnings when thresholds exceeded

**Limitations (acceptable for MVP):**
- Line number tracking would require more complex AST tracking
- Depth calculation requires graph traversal (deferred)
- Doesn't handle all dependency patterns (set_upstream/set_downstream)

---

## 6. File Structure

### 6.1 Project Directory Layout

```
daglinter/
├── .github/
│   └── workflows/
│       ├── ci.yml                 # CI/CD pipeline
│       └── release.yml            # Release automation
├── daglinter/                     # Main package
│   ├── __init__.py
│   ├── __main__.py                # CLI entry point
│   ├── __version__.py             # Version info
│   │
│   ├── cli/                       # CLI components
│   │   ├── __init__.py
│   │   ├── argument_parser.py     # Argparse setup
│   │   └── application.py         # Main CLI application
│   │
│   ├── core/                      # Core logic
│   │   ├── __init__.py
│   │   ├── ast_parser.py          # AST parsing
│   │   ├── config.py              # Configuration management
│   │   ├── file_scanner.py        # File discovery
│   │   ├── linter.py              # Main linting orchestrator
│   │   └── violations.py          # Violation data structures
│   │
│   ├── rules/                     # Linting rules
│   │   ├── __init__.py
│   │   ├── base_rule.py           # Base rule class
│   │   ├── registry.py            # Rule registry
│   │   ├── heavy_imports.py       # DL001
│   │   ├── db_connections.py      # DL002
│   │   ├── missing_docs.py        # DL003
│   │   └── complex_dependencies.py # DL004
│   │
│   ├── formatters/                # Output formatters
│   │   ├── __init__.py
│   │   ├── base.py                # Base formatter
│   │   ├── terminal.py            # Terminal output (Rich)
│   │   ├── json_formatter.py      # JSON output
│   │   └── sarif_formatter.py     # SARIF output
│   │
│   └── utils/                     # Utilities
│       ├── __init__.py
│       └── scope_tracker.py       # Scope analysis helpers
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── conftest.py                # Pytest configuration
│   │
│   ├── unit/                      # Unit tests
│   │   ├── test_ast_parser.py
│   │   ├── test_config.py
│   │   ├── test_file_scanner.py
│   │   └── rules/
│   │       ├── test_heavy_imports.py
│   │       ├── test_db_connections.py
│   │       ├── test_missing_docs.py
│   │       └── test_complex_dependencies.py
│   │
│   ├── integration/               # Integration tests
│   │   ├── test_cli.py
│   │   ├── test_end_to_end.py
│   │   └── test_formatters.py
│   │
│   └── fixtures/                  # Test DAG files
│       ├── valid/
│       │   ├── simple_dag.py
│       │   └── complex_dag.py
│       └── violations/
│           ├── heavy_imports.py
│           ├── db_connection.py
│           └── missing_docs.py
│
├── docs/                          # Documentation
│   ├── rules/                     # Rule documentation
│   │   ├── DL001.md
│   │   ├── DL002.md
│   │   ├── DL003.md
│   │   └── DL004.md
│   ├── configuration.md           # Config guide
│   └── ci-integration.md          # CI/CD examples
│
├── examples/                      # Example configs
│   ├── .daglinter.yml
│   ├── github-actions.yml
│   └── pre-commit-config.yaml
│
├── .daglinter.yml                 # Self-linting config
├── .gitignore
├── .pre-commit-config.yaml
├── LICENSE                        # MIT License
├── README.md                      # Main documentation
├── pyproject.toml                 # Build config + metadata
├── setup.py                       # Setup script (if needed)
└── requirements.txt               # Dependencies
```

### 6.2 Module Organization Principles

1. **Separation of concerns**: CLI, core logic, rules, formatters are independent
2. **Testability**: Each module can be tested in isolation
3. **Extensibility**: Rules and formatters are pluggable
4. **Standard conventions**: Follow Python package best practices

---

## 7. Performance Architecture

### 7.1 Performance Target Breakdown

| Target | Strategy | Implementation |
|--------|----------|----------------|
| <100ms per file | Efficient AST parsing | Use stdlib `ast`, minimal overhead |
| <5s for 100 files | Sequential processing (MVP) | Single-threaded, optimize per-file |
| <200MB memory | Limit memory retention | Process files one at a time, clear violations |

### 7.2 Performance Optimizations

#### 7.2.1 Fast AST Parsing
```python
# Use native ast.parse - already optimized
# No custom parsing logic - leverage stdlib

def parse_file(self, file_path: Path) -> ParseResult:
    # Read entire file at once (faster than line-by-line)
    source_code = file_path.read_text(encoding='utf-8')

    # Parse in one shot
    tree = ast.parse(source_code, filename=str(file_path))

    return ParseResult(ast_tree=tree, success=True)
```

#### 7.2.2 Single-Pass Analysis
```python
# Visit AST only once, run all rules in parallel

class Linter:
    def lint_file(self, file_path: Path) -> List[Violation]:
        # Parse once
        parse_result = self.parser.parse_file(file_path)

        # Create context once
        context = RuleContext(
            file_path=file_path,
            ast_tree=parse_result.ast_tree,
            source_code=parse_result.source_code
        )

        # All rules analyze same AST
        all_violations = []
        for rule in self.rules:
            violations = rule.analyze(context)
            all_violations.extend(violations)

        return all_violations
```

#### 7.2.3 Lazy Loading
```python
# Don't load source code unless needed for snippets
# Don't read files excluded by config
# Don't parse non-.py files
```

### 7.3 Post-MVP: Parallel Processing

```python
# Future enhancement: Process files in parallel

from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count

class ParallelLinter:
    def lint_files(self, file_paths: List[Path]) -> List[Violation]:
        max_workers = min(cpu_count(), len(file_paths))

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            results = executor.map(self.lint_file, file_paths)

        return list(itertools.chain.from_iterable(results))
```

---

## 8. Extensibility Architecture

### 8.1 Plugin Interface Design

**Future: Custom Rules via Plugins**

```python
# pyproject.toml or setup.py
[project.entry-points."daglinter.rules"]
my_custom_rule = "my_package.rules:CustomRule"

# User's custom rule
from daglinter.rules.base_rule import BaseRule

class CustomRule(BaseRule):
    rule_id = "CUSTOM001"
    rule_name = "my-custom-rule"

    def analyze(self, context):
        # User implementation
        return []

# Automatically discovered and registered
```

### 8.2 Configuration Schema for Rules

```yaml
# .daglinter.yml

rules:
  # Built-in rule
  heavy-imports:
    enabled: true
    severity: error
    libraries:
      - pandas
      - custom_lib

  # Custom rule (future)
  my-custom-rule:
    enabled: true
    severity: warning
    custom_param: value
```

### 8.3 Custom Formatter Registration

```python
# Future: Custom output formats

class CustomFormatter(BaseFormatter):
    def format(self, violations, files_scanned):
        # Custom formatting logic
        return custom_output

# Register
from daglinter.formatters import registry
registry.register('custom', CustomFormatter)

# Use
daglinter --format custom my_dags/
```

---

## 9. Integration Points

### 9.1 Exit Codes

```python
class ExitCode(Enum):
    SUCCESS = 0           # No violations
    VIOLATIONS_FOUND = 1  # Violations found
    ERROR = 2             # Tool error (crash, invalid config)

def main():
    try:
        violations = linter.lint()

        if not violations:
            return ExitCode.SUCCESS

        # Check severity
        has_errors = any(v.severity == Severity.ERROR for v in violations)

        if has_errors or fail_on_warning:
            return ExitCode.VIOLATIONS_FOUND

        return ExitCode.SUCCESS

    except Exception as e:
        logger.error(f"Tool error: {e}")
        return ExitCode.ERROR
```

### 9.2 CI/CD Integration Examples

#### GitHub Actions

```yaml
# .github/workflows/daglinter.yml
name: Lint Airflow DAGs

on: [push, pull_request]

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

      - name: Lint DAGs
        run: daglinter --format sarif --output results.sarif dags/

      - name: Upload SARIF results
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: results.sarif
```

#### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/your-org/daglinter
    rev: v1.0.0
    hooks:
      - id: daglinter
        name: Lint Airflow DAGs
        entry: daglinter
        language: python
        types: [python]
        files: ^dags/
```

### 9.3 SARIF Format Specification

```python
# daglinter/formatters/sarif_formatter.py

def format_sarif(violations: List[Violation]) -> dict:
    """Format violations as SARIF 2.1.0."""
    return {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "DAGLinter",
                        "version": "1.0.0",
                        "informationUri": "https://github.com/your-org/daglinter",
                        "rules": [
                            {
                                "id": "DL001",
                                "name": "heavy-imports",
                                "shortDescription": {
                                    "text": "Heavy import at module level"
                                },
                                "helpUri": "https://daglinter.io/rules/DL001"
                            },
                            # ... other rules
                        ]
                    }
                },
                "results": [
                    {
                        "ruleId": v.rule_id,
                        "level": "error" if v.severity == Severity.ERROR else "warning",
                        "message": {
                            "text": v.message
                        },
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {
                                        "uri": str(v.file_path)
                                    },
                                    "region": {
                                        "startLine": v.line,
                                        "startColumn": v.column
                                    }
                                }
                            }
                        ]
                    }
                    for v in violations
                ]
            }
        ]
    }
```

---

## 10. Data Flow

### 10.1 End-to-End Data Flow Diagram

```
[User Input]
    │
    └──> daglinter dags/ --format json
             │
             ▼
    ┌────────────────────┐
    │ Argument Parser    │
    │ - Parse CLI args   │
    │ - Load config file │
    └────────┬───────────┘
             │
             ▼
    ┌────────────────────┐
    │ File Scanner       │
    │ - Find .py files   │
    │ - Apply excludes   │
    └────────┬───────────┘
             │
             └──> [file1.py, file2.py, ...]
                      │
                      ▼
             ┌────────────────────┐
             │ For Each File:     │
             │                    │
             │ 1. Parse to AST    │
             │    ↓               │
             │ 2. Build Context   │
             │    ↓               │
             │ 3. Run Rules       │
             │    ↓               │
             │ 4. Collect Violations│
             └────────┬───────────┘
                      │
                      ▼
             [Violation List]
                      │
                      ▼
    ┌─────────────────────────┐
    │ Formatter (JSON/SARIF)  │
    │ - Serialize violations  │
    │ - Generate output       │
    └────────┬────────────────┘
             │
             ▼
    [JSON/SARIF Output]
             │
             ▼
    [Exit Code: 0, 1, or 2]
```

### 10.2 Rule Execution Flow

```
[AST Tree] ───┐
              │
              ├──> HeavyImportRule.analyze()
              │    └──> [Violation, Violation, ...]
              │
              ├──> DatabaseConnectionRule.analyze()
              │    └──> [Violation, ...]
              │
              ├──> MissingDocsRule.analyze()
              │    └──> [Violation, ...]
              │
              └──> ComplexDependencyRule.analyze()
                   └──> [Violation, ...]

All violations collected ──> Sorted by file/line ──> Formatted
```

---

## 11. Error Handling Strategy

### 11.1 Error Categories

| Error Type | Handling Strategy | User Impact |
|------------|-------------------|-------------|
| **Syntax errors in DAG files** | Catch, report as parse error, continue | File skipped, warning shown |
| **File read errors** | Catch, log, continue | File skipped, warning shown |
| **Invalid configuration** | Fail fast with clear message | Tool exits with error |
| **Rule execution errors** | Catch, log, skip rule for file | Other rules continue |
| **Unhandled exceptions** | Catch at top level, exit gracefully | Tool exits, error logged |

### 11.2 Error Handling Implementation

```python
# Top-level error handling
def main():
    try:
        app = CLIApplication()
        exit_code = app.run()
        sys.exit(exit_code)

    except ConfigurationError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        sys.exit(ExitCode.ERROR)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(ExitCode.ERROR)

    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        if verbose:
            traceback.print_exc()
        sys.exit(ExitCode.ERROR)

# Graceful handling of malformed files
def lint_file(self, file_path: Path) -> LintResult:
    try:
        parse_result = self.parser.parse_file(file_path)

        if not parse_result.success:
            # Syntax error - report but don't crash
            return LintResult(
                file_path=file_path,
                violations=[],
                error=parse_result.error
            )

        # Continue with analysis
        violations = self.run_rules(parse_result)
        return LintResult(file_path=file_path, violations=violations)

    except Exception as e:
        # Unexpected error - log and continue
        logger.error(f"Error linting {file_path}: {e}")
        return LintResult(
            file_path=file_path,
            violations=[],
            error=f"Internal error: {str(e)}"
        )
```

---

## 12. Testing Architecture

### 12.1 Test Pyramid

```
         /\
        /  \      E2E Tests (5%)
       /    \     - Full CLI workflow
      /------\    - CI/CD integration
     /        \
    /          \  Integration Tests (25%)
   /            \ - Rule + formatter combinations
  /--------------\- Config loading + merging
 /                \
/------------------\ Unit Tests (70%)
                    - Individual rule logic
                    - AST parsing
                    - Config validation
                    - Formatter output
```

### 12.2 Test Organization

```python
# tests/unit/rules/test_heavy_imports.py

import pytest
from daglinter.rules.heavy_imports import HeavyImportRule
from daglinter.core.violations import Severity

class TestHeavyImportRule:
    """Test heavy import detection."""

    def test_module_level_import_fails(self):
        """Module-level pandas import should fail."""
        code = """
import pandas as pd

from airflow import DAG

dag = DAG('test')
"""
        violations = run_rule(HeavyImportRule(), code)

        assert len(violations) == 1
        assert violations[0].rule_id == "DL001"
        assert violations[0].severity == Severity.ERROR
        assert "pandas" in violations[0].message

    def test_function_level_import_passes(self):
        """Function-level pandas import should pass."""
        code = """
from airflow import DAG
from airflow.decorators import task

dag = DAG('test')

@task
def process():
    import pandas as pd
    return pd.DataFrame()
"""
        violations = run_rule(HeavyImportRule(), code)

        assert len(violations) == 0

    def test_custom_library_detected(self):
        """Custom heavy library should be detected."""
        rule = HeavyImportRule(config={
            'libraries': ['custom_lib']
        })

        code = "import custom_lib"
        violations = run_rule(rule, code)

        assert len(violations) == 1
        assert "custom_lib" in violations[0].message

# Test helper
def run_rule(rule, code):
    """Helper to run rule on code snippet."""
    tree = ast.parse(code)
    context = RuleContext(
        file_path=Path("test.py"),
        ast_tree=tree,
        source_code=code,
        config={}
    )
    return rule.analyze(context)
```

### 12.3 Integration Test Example

```python
# tests/integration/test_cli.py

def test_cli_end_to_end(tmp_path):
    """Test full CLI workflow."""
    # Create test DAG with violation
    dag_file = tmp_path / "test_dag.py"
    dag_file.write_text("""
import pandas as pd

from airflow import DAG

dag = DAG('test')
""")

    # Run CLI
    result = subprocess.run(
        ['daglinter', str(tmp_path)],
        capture_output=True,
        text=True
    )

    # Verify output
    assert result.returncode == 1  # Violations found
    assert "DL001" in result.stdout
    assert "pandas" in result.stdout
    assert "ERROR" in result.stdout

def test_json_output(tmp_path):
    """Test JSON output format."""
    dag_file = tmp_path / "test_dag.py"
    dag_file.write_text("import pandas")

    result = subprocess.run(
        ['daglinter', '--format', 'json', str(tmp_path)],
        capture_output=True,
        text=True
    )

    output = json.loads(result.stdout)

    assert 'violations' in output
    assert len(output['violations']) > 0
    assert output['violations'][0]['rule_id'] == 'DL001'
```

### 12.4 Performance Testing

```python
# tests/performance/test_benchmarks.py

import pytest
import time

@pytest.mark.benchmark
def test_single_file_performance(benchmark_dag):
    """Single file should parse in <100ms."""
    start = time.perf_counter()

    linter = Linter()
    violations = linter.lint_file(benchmark_dag)

    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 100, f"Took {elapsed_ms}ms, expected <100ms"

@pytest.mark.benchmark
def test_hundred_files_performance(hundred_dags):
    """100 files should parse in <5 seconds."""
    start = time.perf_counter()

    linter = Linter()
    for dag_file in hundred_dags:
        linter.lint_file(dag_file)

    elapsed = time.perf_counter() - start

    assert elapsed < 5.0, f"Took {elapsed}s, expected <5s"
```

---

## 13. Implementation Roadmap

### Week 1-2: Foundation
- [ ] Set up project structure
- [ ] Implement AST parser with error handling
- [ ] Create base rule class and registry
- [ ] Implement HeavyImportRule (DL001)
- [ ] Implement DatabaseConnectionRule (DL002)
- [ ] Unit tests for parser and first two rules
- [ ] Achieve <50ms per file performance

### Week 3-4: Core Features
- [ ] Implement MissingDocsRule (DL003)
- [ ] Implement ComplexDependencyRule (DL004)
- [ ] Build CLI with argparse
- [ ] Implement terminal formatter with Rich
- [ ] File scanner with exclude patterns
- [ ] Integration tests
- [ ] Achieve <100ms per file performance

### Week 5-6: Configuration & Integration
- [ ] Configuration file support (.daglinter.yml)
- [ ] JSON output formatter
- [ ] SARIF output formatter
- [ ] Exit code handling
- [ ] CLI flags (--quiet, --verbose, --format)
- [ ] Performance benchmarking
- [ ] False positive tracking

### Week 7-8: Polish & Release
- [ ] Cross-platform testing
- [ ] Comprehensive documentation
- [ ] CI/CD integration examples
- [ ] Beta testing with 100+ users
- [ ] Bug fixes based on feedback
- [ ] PyPI packaging
- [ ] Public release

---

## 14. Key Design Decisions

### Decision Log

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| **Use stdlib `ast` module** | Zero dependencies, complete Python syntax support | Limited to Python, can't parse other languages |
| **Single-threaded for MVP** | Simpler implementation, sufficient for target performance | Won't scale to 1000+ file repos without parallel processing |
| **Rich library for terminal** | Best-in-class formatting, active maintenance | External dependency, but worth it for UX |
| **YAML for config** | Human-friendly, widely adopted | Need PyYAML dependency |
| **Warning vs Error defaults** | Conservative: errors for performance issues, warnings for style | May need user adjustment via config |
| **No auto-fix in MVP** | Too risky, complex, can introduce bugs | Users must manually fix, but safer |
| **Rule-based (not ML)** | Deterministic, explainable, fast | Won't catch novel patterns like ML could |

---

## Conclusion

This architecture provides a solid foundation for building DAGLinter MVP. Key strengths:

1. **Modularity**: Clean separation enables parallel development and testing
2. **Performance**: Architecture supports <100ms per file target
3. **Extensibility**: Plugin system designed from the start
4. **Maintainability**: Type hints, clear abstractions, comprehensive tests
5. **User Experience**: Rich terminal output, helpful error messages

**Next Steps:**
1. Review and approve this architecture
2. Create implementation tasks from roadmap
3. Begin Sprint 1 development

**Success Metrics:**
- Code coverage ≥85%
- Performance targets met
- False positive rate <10% (MVP), <5% (post-MVP)
- All 4 MVP rules functional by Week 4
