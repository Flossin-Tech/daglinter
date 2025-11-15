"""SARIF formatter for GitHub Code Scanning integration."""

import json
from typing import List

from daglinter.core.models import Severity, Violation


class SARIFFormatter:
    """Formats violations as SARIF 2.1.0."""

    @staticmethod
    def format_violations(
        violations: List[Violation], version: str = "0.1.0"
    ) -> str:
        """
        Format violations as SARIF 2.1.0.

        Args:
            violations: List of violations
            version: Tool version

        Returns:
            SARIF JSON string
        """
        # Define rules
        rules = [
            {
                "id": "DL001",
                "name": "heavy-imports",
                "shortDescription": {"text": "Heavy import at module level"},
                "fullDescription": {
                    "text": "Heavy libraries imported at module level slow DAG parsing"
                },
                "helpUri": "https://github.com/Flossin-Tech/daglinter#dl001",
            },
            {
                "id": "DL002",
                "name": "db-connections",
                "shortDescription": {"text": "Database connection at module level"},
                "fullDescription": {
                    "text": "Database connections at module level create resource leaks"
                },
                "helpUri": "https://github.com/Flossin-Tech/daglinter#dl002",
            },
            {
                "id": "DL003",
                "name": "missing-docs",
                "shortDescription": {"text": "Missing DAG documentation"},
                "fullDescription": {
                    "text": "DAGs without documentation are hard to maintain"
                },
                "helpUri": "https://github.com/Flossin-Tech/daglinter#dl003",
            },
            {
                "id": "DL004",
                "name": "complex-dependencies",
                "shortDescription": {"text": "Complex task dependencies"},
                "fullDescription": {
                    "text": "Overly complex dependency patterns reduce maintainability"
                },
                "helpUri": "https://github.com/Flossin-Tech/daglinter#dl004",
            },
        ]

        # Convert violations to SARIF results
        results = []
        for v in violations:
            level = "error" if v.severity == Severity.ERROR else "warning"
            if v.severity == Severity.INFO:
                level = "note"

            result = {
                "ruleId": v.rule_id,
                "level": level,
                "message": {"text": v.message},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": str(v.file_path)},
                            "region": {
                                "startLine": v.line,
                                "startColumn": v.column + 1,  # SARIF is 1-indexed
                            },
                        }
                    }
                ],
            }

            if v.suggestion:
                result["fixes"] = [
                    {"description": {"text": v.suggestion}, "artifactChanges": []}
                ]

            results.append(result)

        sarif = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "DAGLinter",
                            "version": version,
                            "informationUri": "https://github.com/Flossin-Tech/daglinter",
                            "rules": rules,
                        }
                    },
                    "results": results,
                }
            ],
        }

        return json.dumps(sarif, indent=2)
