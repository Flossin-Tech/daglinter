"""JSON formatter for machine-readable output."""

import json
from datetime import datetime
from typing import List

from daglinter.core.models import Violation


class JSONFormatter:
    """Formats violations as JSON."""

    @staticmethod
    def format_violations(
        violations: List[Violation], files_scanned: int, version: str = "0.1.0"
    ) -> str:
        """
        Format violations as JSON.

        Args:
            violations: List of violations
            files_scanned: Number of files scanned
            version: Tool version

        Returns:
            JSON string
        """
        errors = sum(1 for v in violations if v.severity.value == "error")
        warnings = sum(1 for v in violations if v.severity.value == "warning")
        infos = sum(1 for v in violations if v.severity.value == "info")

        output = {
            "version": version,
            "scan_time": datetime.utcnow().isoformat() + "Z",
            "summary": {
                "files_scanned": files_scanned,
                "errors": errors,
                "warnings": warnings,
                "info": infos,
                "total_violations": len(violations),
            },
            "violations": [
                {
                    "file": str(v.file_path),
                    "line": v.line,
                    "column": v.column,
                    "severity": v.severity.value,
                    "rule_id": v.rule_id,
                    "rule_name": v.rule_name,
                    "message": v.message,
                    "suggestion": v.suggestion,
                    "code_snippet": v.code_snippet,
                }
                for v in violations
            ],
        }

        return json.dumps(output, indent=2)
