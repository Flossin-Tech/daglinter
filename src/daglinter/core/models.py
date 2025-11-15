"""Data models for DAGLinter."""

import ast
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Optional


class Severity(Enum):
    """Severity levels for violations."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    def __str__(self) -> str:
        """Return string representation."""
        return self.value


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

    def __post_init__(self) -> None:
        """Validate violation data."""
        if not self.rule_id:
            raise ValueError("rule_id cannot be empty")
        if not self.message:
            raise ValueError("message cannot be empty")
        if self.line < 0:
            raise ValueError("line must be non-negative")
        if self.column < 0:
            raise ValueError("column must be non-negative")


@dataclass
class RuleContext:
    """Context provided to rules during analysis."""

    file_path: Path
    ast_tree: ast.AST
    source_code: str
    config: Dict[str, any]

    def get_line(self, line_number: int) -> Optional[str]:
        """
        Get a specific line from the source code.

        Args:
            line_number: Line number (1-indexed)

        Returns:
            The line content or None if out of range
        """
        try:
            lines = self.source_code.split("\n")
            if 0 < line_number <= len(lines):
                return lines[line_number - 1]
        except Exception:
            pass
        return None


@dataclass
class ParseResult:
    """Result of parsing a Python file."""

    file_path: Path
    ast_tree: Optional[ast.AST]
    source_code: Optional[str]
    success: bool
    error: Optional[str] = None
    parse_time_ms: float = 0.0
