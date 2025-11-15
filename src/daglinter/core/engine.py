"""Linting engine that orchestrates rule execution."""

from pathlib import Path
from typing import Dict, List, Optional

from daglinter.core.models import RuleContext, Violation
from daglinter.core.parser import ASTParser
from daglinter.rules.base import BaseRule, registry
from daglinter.rules.complex_deps import ComplexDependencyRule
from daglinter.rules.database_calls import DatabaseConnectionRule
from daglinter.rules.heavy_imports import HeavyImportRule
from daglinter.rules.missing_docs import MissingDocsRule


class LintEngine:
    """Main linting engine that coordinates parsing and rule execution."""

    def __init__(self, config: Optional[Dict[str, any]] = None):
        """
        Initialize the linting engine.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.parser = ASTParser()

        # Register all built-in rules
        self._register_rules()

        # Get enabled rules based on config
        self.rules = registry.get_enabled_rules(self.config)

    def _register_rules(self) -> None:
        """Register all built-in linting rules."""
        registry.register(HeavyImportRule)
        registry.register(DatabaseConnectionRule)
        registry.register(MissingDocsRule)
        registry.register(ComplexDependencyRule)

    def lint_file(self, file_path: Path) -> List[Violation]:
        """
        Lint a single Python file.

        Args:
            file_path: Path to the file to lint

        Returns:
            List of violations found
        """
        # Parse the file
        parse_result = self.parser.parse_file(file_path)

        # If parsing failed, return empty list (error already logged)
        if not parse_result.success:
            return []

        # Create context for rules
        context = RuleContext(
            file_path=file_path,
            ast_tree=parse_result.ast_tree,
            source_code=parse_result.source_code,
            config=self.config,
        )

        # Run all enabled rules
        violations = []
        for rule in self.rules:
            try:
                rule_violations = rule.analyze(context)
                violations.extend(rule_violations)
            except Exception as e:
                # Log error but continue with other rules
                print(f"Error running rule {rule.rule_id} on {file_path}: {e}")

        return violations

    def lint_files(self, file_paths: List[Path]) -> Dict[Path, List[Violation]]:
        """
        Lint multiple Python files.

        Args:
            file_paths: List of file paths to lint

        Returns:
            Dictionary mapping file paths to their violations
        """
        results = {}

        for file_path in file_paths:
            violations = self.lint_file(file_path)
            if violations:
                results[file_path] = violations

        return results

    def get_all_violations(
        self, file_paths: List[Path]
    ) -> tuple[List[Violation], int]:
        """
        Get all violations from multiple files.

        Args:
            file_paths: List of file paths to lint

        Returns:
            Tuple of (all violations, number of files scanned)
        """
        all_violations = []
        files_scanned = 0

        for file_path in file_paths:
            violations = self.lint_file(file_path)
            all_violations.extend(violations)
            files_scanned += 1

        return all_violations, files_scanned
