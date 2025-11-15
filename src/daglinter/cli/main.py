"""Main CLI entry point for DAGLinter."""

import argparse
import sys
from pathlib import Path
from typing import List

from daglinter import __version__
from daglinter.core.config import Config, ConfigLoader
from daglinter.core.engine import LintEngine
from daglinter.core.models import Severity
from daglinter.formatters.json import JSONFormatter
from daglinter.formatters.sarif import SARIFFormatter
from daglinter.formatters.terminal import TerminalFormatter


def find_python_files(path: Path, exclude_patterns: List[str]) -> List[Path]:
    """
    Find all Python files in a directory or return single file.

    Args:
        path: File or directory path
        exclude_patterns: Patterns to exclude

    Returns:
        List of Python file paths
    """
    if path.is_file():
        if path.suffix == ".py":
            return [path]
        else:
            return []

    # Recursively find Python files
    python_files = []
    for py_file in path.rglob("*.py"):
        # Check if file matches any exclude pattern
        should_exclude = False
        for pattern in exclude_patterns:
            # Simple pattern matching (can be enhanced with fnmatch)
            if pattern.replace("**", "").replace("*", "") in str(py_file):
                should_exclude = True
                break

        if not should_exclude:
            python_files.append(py_file)

    return python_files


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI."""
    parser = argparse.ArgumentParser(
        prog="daglinter",
        description="A static analysis tool for Apache Airflow DAG files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  daglinter my_dag.py              # Lint a single file
  daglinter dags/                  # Lint all Python files in directory
  daglinter --format json dags/    # Output JSON format
  daglinter --config .daglinter.yml dags/  # Use specific config file

Exit codes:
  0 - No violations found
  1 - Violations found
  2 - Error occurred
        """,
    )

    parser.add_argument(
        "path",
        type=Path,
        help="File or directory to lint",
    )

    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (.daglinter.yml)",
    )

    parser.add_argument(
        "--format",
        choices=["terminal", "json", "sarif"],
        default="terminal",
        help="Output format (default: terminal)",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Output file (default: stdout)",
    )

    parser.add_argument(
        "--color",
        choices=["auto", "always", "never"],
        default="auto",
        help="Color output mode (default: auto)",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress all output except violations",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser


def main() -> int:
    """
    Main entry point for CLI.

    Returns:
        Exit code (0=success, 1=violations, 2=error)
    """
    parser = create_parser()
    args = parser.parse_args()

    try:
        # Load configuration
        config = ConfigLoader.load(args.config)

        # Merge CLI arguments
        config = config.merge_cli_args(
            output_format=args.format,
            output_file=args.output,
            color=args.color,
            quiet=args.quiet,
            verbose=args.verbose,
        )

        # Validate path
        if not args.path.exists():
            print(f"Error: Path does not exist: {args.path}", file=sys.stderr)
            return 2

        # Find Python files to lint
        python_files = find_python_files(args.path, config.exclude)

        if not python_files:
            print(f"No Python files found in {args.path}", file=sys.stderr)
            return 2

        # Create linting engine
        engine = LintEngine(config.to_dict())

        # Lint files
        all_violations, files_scanned = engine.get_all_violations(python_files)

        # Format output
        if args.format == "json":
            formatter = JSONFormatter()
            output = formatter.format_violations(
                all_violations, files_scanned, __version__
            )
            if args.output:
                args.output.write_text(output)
            else:
                print(output)

        elif args.format == "sarif":
            formatter = SARIFFormatter()
            output = formatter.format_violations(all_violations, __version__)
            if args.output:
                args.output.write_text(output)
            else:
                print(output)

        else:  # terminal
            formatter = TerminalFormatter(color=config.color)
            formatter.format_violations(all_violations, files_scanned)

        # Determine exit code
        has_errors = any(v.severity == Severity.ERROR for v in all_violations)

        if has_errors:
            return 1
        elif all_violations:
            # Has warnings but no errors
            return 0
        else:
            # No violations
            return 0

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 2

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose if hasattr(args, "verbose") else False:
            import traceback

            traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
