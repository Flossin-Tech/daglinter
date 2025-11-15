"""AST parsing module for Python files."""

import ast
import time
from pathlib import Path
from typing import Optional

from daglinter.core.models import ParseResult


class ASTParser:
    """Parses Python files into AST for analysis."""

    def parse_file(self, file_path: Path) -> ParseResult:
        """
        Parse a Python file into an AST.

        Args:
            file_path: Path to Python file

        Returns:
            ParseResult with AST or error information
        """
        start_time = time.perf_counter()

        try:
            source_code = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source_code, filename=str(file_path))

            parse_time = (time.perf_counter() - start_time) * 1000

            return ParseResult(
                file_path=file_path,
                ast_tree=tree,
                source_code=source_code,
                success=True,
                parse_time_ms=parse_time,
            )

        except SyntaxError as e:
            parse_time = (time.perf_counter() - start_time) * 1000
            error_msg = f"Syntax error at line {e.lineno}: {e.msg}"
            return ParseResult(
                file_path=file_path,
                ast_tree=None,
                source_code=None,
                success=False,
                error=error_msg,
                parse_time_ms=parse_time,
            )

        except UnicodeDecodeError as e:
            parse_time = (time.perf_counter() - start_time) * 1000
            return ParseResult(
                file_path=file_path,
                ast_tree=None,
                source_code=None,
                success=False,
                error=f"Encoding error: {str(e)}",
                parse_time_ms=parse_time,
            )

        except Exception as e:
            parse_time = (time.perf_counter() - start_time) * 1000
            return ParseResult(
                file_path=file_path,
                ast_tree=None,
                source_code=None,
                success=False,
                error=f"Parse error: {str(e)}",
                parse_time_ms=parse_time,
            )

    def parse_string(self, source_code: str, filename: str = "<string>") -> ParseResult:
        """
        Parse Python source code string into an AST.

        Args:
            source_code: Python source code
            filename: Optional filename for error messages

        Returns:
            ParseResult with AST or error information
        """
        start_time = time.perf_counter()

        try:
            tree = ast.parse(source_code, filename=filename)

            parse_time = (time.perf_counter() - start_time) * 1000

            return ParseResult(
                file_path=Path(filename),
                ast_tree=tree,
                source_code=source_code,
                success=True,
                parse_time_ms=parse_time,
            )

        except SyntaxError as e:
            parse_time = (time.perf_counter() - start_time) * 1000
            error_msg = f"Syntax error at line {e.lineno}: {e.msg}"
            return ParseResult(
                file_path=Path(filename),
                ast_tree=None,
                source_code=source_code,
                success=False,
                error=error_msg,
                parse_time_ms=parse_time,
            )

        except Exception as e:
            parse_time = (time.perf_counter() - start_time) * 1000
            return ParseResult(
                file_path=Path(filename),
                ast_tree=None,
                source_code=source_code,
                success=False,
                error=f"Parse error: {str(e)}",
                parse_time_ms=parse_time,
            )
