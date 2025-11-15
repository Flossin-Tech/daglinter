"""DL003: Missing DAG Documentation Rule."""

import ast
from typing import List, Optional

from daglinter.core.models import RuleContext, Severity, Violation
from daglinter.rules.base import BaseRule


class MissingDocsRule(BaseRule, ast.NodeVisitor):
    """Detect DAGs without documentation."""

    rule_id = "DL003"
    rule_name = "missing-docs"
    default_severity = Severity.WARNING

    def __init__(self, config=None):
        """Initialize the missing docs rule."""
        super().__init__(config)
        self.violations: List[Violation] = []
        self.context: RuleContext = None
        self.min_length = self.config.get("min_length", 20)
        self.checked_nodes = set()  # Track checked nodes to avoid duplicates

    def analyze(self, context: RuleContext) -> List[Violation]:
        """Analyze DAG documentation."""
        self.violations = []
        self.context = context
        self.checked_nodes = set()

        self.visit(context.ast_tree)

        return self.violations

    def visit_Call(self, node: ast.Call) -> None:
        """Check DAG constructor calls."""
        # Avoid checking the same node twice
        node_id = id(node)
        if node_id not in self.checked_nodes:
            if self._is_dag_constructor(node):
                doc_param = self._get_doc_parameter(node)

                if not doc_param or not self._is_valid_doc(doc_param):
                    self._create_docs_violation(node)
                    self.checked_nodes.add(node_id)

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Check DAG assignments - handled by visit_Call."""
        # Don't need to do anything here - visit_Call will handle it
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        """Check DAG context managers - handled by visit_Call."""
        # Don't need to do anything here - visit_Call will handle it
        self.generic_visit(node)

    def _is_dag_constructor(self, node: ast.Call) -> bool:
        """Check if call is DAG constructor."""
        # Check for: DAG(...)
        if isinstance(node.func, ast.Name) and node.func.id == "DAG":
            return True

        # Check for: airflow.DAG(...)
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "DAG":
                return True

        return False

    def _get_doc_parameter(self, node: ast.Call) -> Optional[str]:
        """Extract doc_md or description parameter."""
        # Check keyword arguments
        for keyword in node.keywords:
            if keyword.arg in ("doc_md", "description", "doc"):
                # Python 3.8+ uses ast.Constant
                if isinstance(keyword.value, ast.Constant):
                    return keyword.value.value
                # Python 3.7 compatibility
                elif isinstance(keyword.value, ast.Str):
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
        placeholders = ["todo", "tbd", "fixme", "xxx", "placeholder", "test"]
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
                "Add doc_md or description parameter with DAG purpose, "
                f"schedule, and owner. Minimum length: {self.min_length} characters. "
                "Example: doc_md='## Purpose\\nThis DAG processes daily sales data'"
            ),
        )
        self.violations.append(violation)
