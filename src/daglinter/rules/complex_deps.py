"""DL004: Complex Dependency Pattern Detection Rule."""

import ast
from collections import defaultdict
from typing import Dict, List, Set

from daglinter.core.models import RuleContext, Severity, Violation
from daglinter.rules.base import BaseRule


class ComplexDependencyRule(BaseRule, ast.NodeVisitor):
    """Detect overly complex task dependency patterns."""

    rule_id = "DL004"
    rule_name = "complex-dependencies"
    default_severity = Severity.WARNING

    def __init__(self, config=None):
        """Initialize the complex dependency rule."""
        super().__init__(config)
        self.violations: List[Violation] = []
        self.context: RuleContext = None

        # Configurable thresholds
        self.max_fan_out = self.config.get("max_fan_out", 10)
        self.max_fan_in = self.config.get("max_fan_in", 10)

        # Dependency graph
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_deps: Dict[str, Set[str]] = defaultdict(set)
        self.task_nodes: Dict[str, ast.AST] = {}

    def analyze(self, context: RuleContext) -> List[Violation]:
        """Analyze task dependencies."""
        self.violations = []
        self.context = context
        self.dependencies = defaultdict(set)
        self.reverse_deps = defaultdict(set)
        self.task_nodes = {}

        # Build dependency graph
        self.visit(context.ast_tree)

        # Check for complex patterns
        self._check_fan_out()
        self._check_fan_in()

        return self.violations

    def visit_BinOp(self, node: ast.BinOp) -> None:
        """Check >> and << operators for dependencies."""
        if isinstance(node.op, ast.RShift):  # >>
            self._add_dependency(node, node.left, node.right)
        elif isinstance(node.op, ast.LShift):  # <<
            self._add_dependency(node, node.right, node.left)

        self.generic_visit(node)

    def _add_dependency(
        self, node: ast.AST, upstream: ast.AST, downstream: ast.AST
    ) -> None:
        """Add dependency to graph."""
        # Extract task names
        upstream_tasks = self._extract_task_names(upstream)
        downstream_tasks = self._extract_task_names(downstream)

        for up in upstream_tasks:
            for down in downstream_tasks:
                self.dependencies[up].add(down)
                self.reverse_deps[down].add(up)
                # Store node references for error reporting
                if up not in self.task_nodes:
                    self.task_nodes[up] = node
                if down not in self.task_nodes:
                    self.task_nodes[down] = node

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
        elif isinstance(node, ast.BinOp):
            # Handle chained operations: a >> b >> c
            names.extend(self._extract_task_names(node.left))
            names.extend(self._extract_task_names(node.right))

        return names

    def _check_fan_out(self) -> None:
        """Check for excessive downstream dependencies."""
        for task, downstream in self.dependencies.items():
            if len(downstream) > self.max_fan_out:
                node = self.task_nodes.get(task)
                if node:
                    violation = self.create_violation(
                        context=self.context,
                        node=node,
                        message=(
                            f"Task '{task}' has {len(downstream)} downstream "
                            f"dependencies (max: {self.max_fan_out})"
                        ),
                        suggestion=(
                            "Consider using TaskGroup to organize related tasks "
                            "or dynamic task mapping for better maintainability. "
                            "Excessive fan-out makes DAGs harder to understand and debug."
                        ),
                    )
                    self.violations.append(violation)

    def _check_fan_in(self) -> None:
        """Check for excessive upstream dependencies."""
        for task, upstream in self.reverse_deps.items():
            if len(upstream) > self.max_fan_in:
                node = self.task_nodes.get(task)
                if node:
                    violation = self.create_violation(
                        context=self.context,
                        node=node,
                        message=(
                            f"Task '{task}' has {len(upstream)} upstream "
                            f"dependencies (max: {self.max_fan_in})"
                        ),
                        suggestion=(
                            "Consider refactoring to reduce coupling or "
                            "use intermediate aggregation tasks. "
                            "Excessive fan-in indicates tight coupling."
                        ),
                    )
                    self.violations.append(violation)
