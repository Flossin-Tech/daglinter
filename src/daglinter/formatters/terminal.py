"""Terminal formatter using Rich for colored output."""

from pathlib import Path
from typing import Dict, List

from rich.console import Console
from rich.table import Table

from daglinter.core.models import Severity, Violation


class TerminalFormatter:
    """Formats violations for terminal output using Rich."""

    def __init__(self, color: str = "auto"):
        """
        Initialize terminal formatter.

        Args:
            color: Color mode (auto, always, never)
        """
        self.console = Console(
            force_terminal=(color == "always"), no_color=(color == "never")
        )

    def format_violations(
        self, violations: List[Violation], files_scanned: int
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
        by_file: Dict[Path, List[Violation]] = {}
        for v in violations:
            if v.file_path not in by_file:
                by_file[v.file_path] = []
            by_file[v.file_path].append(v)

        # Print violations per file
        self.console.print("\n[bold]Linting Results[/bold]")
        self.console.rule()

        for file_path, file_violations in sorted(by_file.items()):
            self.console.print(f"\n[bold cyan]{file_path}[/bold cyan]")

            for violation in sorted(file_violations, key=lambda v: v.line):
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
            f"{violation.severity.value.upper()}[/{color}] "
            f"(line {violation.line}:{violation.column})"
        )
        self.console.print(f"    {violation.message}")

        # Code snippet
        if violation.code_snippet:
            self.console.print(f"    [dim]→ {violation.code_snippet}[/dim]")

        # Suggestion
        if violation.suggestion:
            self.console.print(
                f"    [italic dim]Suggestion: {violation.suggestion}[/italic dim]"
            )
        self.console.print()

    def _print_summary(self, violations: List[Violation], files_scanned: int) -> None:
        """Print summary statistics."""
        errors = sum(1 for v in violations if v.severity == Severity.ERROR)
        warnings = sum(1 for v in violations if v.severity == Severity.WARNING)
        infos = sum(1 for v in violations if v.severity == Severity.INFO)
        files_with_violations = len(set(v.file_path for v in violations))
        clean_files = files_scanned - files_with_violations

        self.console.print("[bold]Summary[/bold]")
        self.console.print(f"  Files scanned: {files_scanned}")

        if clean_files > 0:
            self.console.print(f"  [green]✓ Clean files: {clean_files}[/green]")

        if files_with_violations > 0:
            self.console.print(
                f"  [yellow]Files with issues: {files_with_violations}[/yellow]"
            )

        if errors > 0:
            self.console.print(f"  [red]✗ Errors: {errors}[/red]")

        if warnings > 0:
            self.console.print(f"  [yellow]⚠ Warnings: {warnings}[/yellow]")

        if infos > 0:
            self.console.print(f"  [blue]ℹ Info: {infos}[/blue]")

        self.console.print()

        if errors > 0:
            self.console.print(
                f"[bold red]✗ Linting failed with {errors} error(s)[/bold red]"
            )
        elif warnings > 0:
            self.console.print(
                f"[bold yellow]⚠ Linting passed with {warnings} warning(s)[/bold yellow]"
            )
        else:
            self.console.print("[bold green]✓ All checks passed![/bold green]")

    def _print_success(self, files_scanned: int) -> None:
        """Print success message when no violations found."""
        self.console.print()
        self.console.print(
            f"[bold green]✓ All {files_scanned} file(s) passed linting![/bold green]"
        )
        self.console.print()
