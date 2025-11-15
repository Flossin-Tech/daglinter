"""Scope tracking utilities for AST analysis."""

import ast
from typing import List


class ScopeTracker(ast.NodeVisitor):
    """Helper to track scope during AST traversal."""

    def __init__(self) -> None:
        """Initialize the scope tracker."""
        self.scope_stack: List[ast.AST] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track entry into function scope."""
        self.scope_stack.append(node)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Track entry into async function scope."""
        self.scope_stack.append(node)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Track entry into class scope."""
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

    @property
    def scope_depth(self) -> int:
        """Get current scope depth."""
        return len(self.scope_stack)
