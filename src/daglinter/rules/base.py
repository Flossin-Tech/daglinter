"""Base rule class and rule registry for DAGLinter."""

import ast
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type

from daglinter.core.models import RuleContext, Severity, Violation


class BaseRule(ABC):
    """Base class for all linting rules."""

    # Class attributes - override in subclasses
    rule_id: str = "DL000"
    rule_name: str = "base-rule"
    default_severity: Severity = Severity.ERROR

    def __init__(self, config: Optional[Dict[str, any]] = None):
        """
        Initialize rule with optional configuration.

        Args:
            config: Rule-specific configuration
        """
        self.config = config or {}
        severity_str = self.config.get("severity", self.default_severity.value)
        self.severity = Severity(severity_str)
        self.enabled = self.config.get("enabled", True)

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
        suggestion: Optional[str] = None,
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
            line=getattr(node, "lineno", 0),
            column=getattr(node, "col_offset", 0),
            message=message,
            suggestion=suggestion,
            code_snippet=self._extract_code_snippet(context, node),
        )

    def _extract_code_snippet(
        self, context: RuleContext, node: ast.AST
    ) -> Optional[str]:
        """Extract source code for the violating line."""
        try:
            if hasattr(node, "lineno"):
                return context.get_line(node.lineno)
        except Exception:
            pass
        return None


class RuleRegistry:
    """Central registry for all linting rules."""

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._rules: Dict[str, Type[BaseRule]] = {}

    def register(self, rule_class: Type[BaseRule]) -> None:
        """
        Register a rule class.

        Args:
            rule_class: Rule class to register
        """
        self._rules[rule_class.rule_id] = rule_class

    def get_enabled_rules(
        self, config: Optional[Dict[str, any]] = None
    ) -> List[BaseRule]:
        """
        Get instances of enabled rules based on config.

        Args:
            config: Configuration dictionary

        Returns:
            List of instantiated, enabled rules
        """
        if config is None:
            config = {}

        rules = []
        rule_configs = config.get("rules", {})

        for rule_id, rule_class in self._rules.items():
            # Get config for this specific rule
            rule_config = rule_configs.get(rule_class.rule_name, {"enabled": True})

            # Instantiate the rule
            rule_instance = rule_class(config=rule_config)

            # Only add if enabled
            if rule_instance.enabled:
                rules.append(rule_instance)

        return rules

    def get_all_rule_ids(self) -> List[str]:
        """Get list of all registered rule IDs."""
        return list(self._rules.keys())


# Global registry instance
registry = RuleRegistry()
