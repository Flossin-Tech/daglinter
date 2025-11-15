"""DL002: Database Connection Detection Rule."""

import ast
from typing import List, Set, Tuple

from daglinter.core.models import RuleContext, Severity, Violation
from daglinter.rules.base import BaseRule


class DatabaseConnectionRule(BaseRule, ast.NodeVisitor):
    """Detect database connections outside task context."""

    rule_id = "DL002"
    rule_name = "db-connections"
    default_severity = Severity.ERROR

    # Patterns: (module, function_name)
    DB_CONNECTION_PATTERNS = [
        ("psycopg2", "connect"),
        ("pymongo", "MongoClient"),
        ("mysql.connector", "connect"),
        ("sqlite3", "connect"),
        ("sqlalchemy", "create_engine"),
        ("pymssql", "connect"),
        ("cx_Oracle", "connect"),
        ("redis", "Redis"),
        ("redis", "StrictRedis"),
    ]

    # Airflow hooks are OK
    AIRFLOW_HOOK_MODULES = {
        "airflow.hooks",
        "airflow.providers",
    }

    def __init__(self, config=None):
        """Initialize the database connection rule."""
        super().__init__(config)
        self.violations: List[Violation] = []
        self.context: RuleContext = None
        self.scope_depth = 0

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

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Track entry into class scope."""
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
        func_name = self._get_call_name(node)

        if not func_name:
            return False

        # Check against patterns
        for module, function in self.DB_CONNECTION_PATTERNS:
            # Check for module.function() pattern
            if func_name.endswith(f"{module}.{function}"):
                return True
            # Check for function() where module is imported
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

            return ".".join(reversed(parts))

        return ""

    def _module_imported(self, module: str) -> bool:
        """Check if module is imported (simplified check)."""
        # Simplified implementation - checks source code for import
        source = self.context.source_code
        return f"import {module}" in source or f"from {module}" in source

    def _create_db_violation(self, node: ast.Call) -> None:
        """Create violation for database connection."""
        func_name = self._get_call_name(node)

        violation = self.create_violation(
            context=self.context,
            node=node,
            message=f"Database connection '{func_name}()' at module level",
            suggestion=(
                "Use Airflow Hooks inside task functions instead. "
                "Database connections at module level create resource leaks "
                "and slow DAG parsing. Example: "
                "PostgresHook(postgres_conn_id='my_conn').get_conn()"
            ),
        )
        self.violations.append(violation)
