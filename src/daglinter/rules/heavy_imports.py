"""DL001: Heavy Import Detection Rule."""

import ast
from typing import List, Set

from daglinter.core.models import RuleContext, Severity, Violation
from daglinter.rules.base import BaseRule


class HeavyImportRule(BaseRule, ast.NodeVisitor):
    """Detect heavy libraries imported at module level."""

    rule_id = "DL001"
    rule_name = "heavy-imports"
    default_severity = Severity.ERROR

    DEFAULT_HEAVY_LIBRARIES = {
        "pandas",
        "numpy",
        "sklearn",
        "tensorflow",
        "torch",
        "matplotlib",
        "seaborn",
        "plotly",
        "scipy",
        "cv2",
        "PIL",
        "keras",
        "xgboost",
        "lightgbm",
    }

    def __init__(self, config=None):
        """Initialize the heavy import rule."""
        super().__init__(config)
        self.violations: List[Violation] = []
        self.context: RuleContext = None
        self.scope_depth = 0

        # Get configured heavy libraries
        custom_libs = self.config.get("libraries", [])
        if custom_libs:
            self.heavy_libraries = set(custom_libs)
        else:
            self.heavy_libraries = self.DEFAULT_HEAVY_LIBRARIES.copy()

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

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Track entry into class scope."""
        self.scope_depth += 1
        self.generic_visit(node)
        self.scope_depth -= 1

    def visit_Import(self, node: ast.Import) -> None:
        """Check 'import X' statements."""
        if self.scope_depth == 0:  # Module level
            for alias in node.names:
                base_module = alias.name.split(".")[0]
                if base_module in self.heavy_libraries:
                    self._create_import_violation(node, alias.name)

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check 'from X import Y' statements."""
        if self.scope_depth == 0 and node.module:  # Module level
            base_module = node.module.split(".")[0]
            if base_module in self.heavy_libraries:
                self._create_import_violation(node, node.module)

        self.generic_visit(node)

    def _create_import_violation(self, node: ast.AST, module_name: str) -> None:
        """Create a violation for a heavy import."""
        violation = self.create_violation(
            context=self.context,
            node=node,
            message=f"Heavy import '{module_name}' at module level may slow DAG parsing",
            suggestion=(
                f"Move 'import {module_name}' inside your task function "
                "to avoid slowing DAG parsing. Heavy libraries should only be "
                "imported when tasks execute, not during DAG file parsing."
            ),
        )
        self.violations.append(violation)
