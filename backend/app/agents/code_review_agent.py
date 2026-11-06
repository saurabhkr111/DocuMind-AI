import re

from pydantic import BaseModel

from backend.app.agents.base_agent import BaseAgent
from backend.app.schemas.agent import (
    AgentInput,
    AgentName,
    AgentFinding,
    FindingSeverity,
    CodeReviewResult,
)


class CodeReviewAgent(BaseAgent):
    """
    Reviews supplied GitHub pull request diffs.

    Performs deterministic pattern-based checks.
    It does not execute repository code.
    """

    agent_name = AgentName.CODE_REVIEW

    # Potential security and code-quality patterns.
    RULES = [
        {
            "pattern": re.compile(
                r"""(?i)\b(?:api_key|api_secret|secret_key|password|access_token)\s*=\s*["'][^"']{6,}["']"""
            ),
            "title": "Potential hardcoded credential",
            "description": (
                "An assignment appears to contain a hardcoded "
                "credential. Verify whether the value is sensitive."
            ),
            "severity": FindingSeverity.HIGH,
            "category": "Security",
            "recommendation": (
                "Move credentials into environment variables or "
                "a secure secrets manager. Rotate the credential "
                "if it is real and has been exposed."
            ),
        },
        {
            "pattern": re.compile(r"\beval\s*\("),
            "title": "Potential unsafe eval() usage",
            "description": (
                "The added code uses eval(). Dynamic evaluation "
                "of untrusted input can introduce security risks."
            ),
            "severity": FindingSeverity.HIGH,
            "category": "Security",
            "recommendation": (
                "Avoid eval() where possible. Use safer parsing "
                "or explicit input validation."
            ),
        },
        {
            "pattern": re.compile(r"\bexec\s*\("),
            "title": "Potential unsafe exec() usage",
            "description": (
                "The added code uses exec(). Dynamic code execution "
                "can introduce security risks."
            ),
            "severity": FindingSeverity.HIGH,
            "category": "Security",
            "recommendation": (
                "Avoid executing dynamically generated code. "
                "Use explicit functions and controlled operations."
            ),
        },
        {
            "pattern": re.compile(r"\bverify\s*=\s*False\b"),
            "title": "TLS certificate verification disabled",
            "description": (
                "TLS certificate verification appears to be disabled. "
                "This may expose network communication to interception."
            ),
            "severity": FindingSeverity.MEDIUM,
            "category": "Security",
            "recommendation": (
                "Keep certificate verification enabled. "
                "Configure trusted certificates when necessary."
            ),
        },
        {
            "pattern": re.compile(r"\bprint\s*\("),
            "title": "Potential debug print statement",
            "description": (
                "A print statement was detected in the added code. "
                "Check whether it should be replaced with structured logging."
            ),
            "severity": FindingSeverity.LOW,
            "category": "Code Quality",
            "recommendation": (
                "Use the application's logging framework and "
                "avoid logging sensitive information."
            ),
        },
    ]

    async def execute(
        self,
        agent_input: AgentInput
    ) -> BaseModel:

        changed_files = agent_input.context.get(
            "changed_files",
            []
        )

        if not isinstance(changed_files, list):
            raise ValueError("changed_files must be a list.")

        findings = []

        for changed_file in changed_files:

            if not isinstance(changed_file, dict):
                raise ValueError(
                    "Each changed file must be an object."
                )

            file_path = changed_file.get("filename")

            if not isinstance(file_path, str) or not file_path.strip():
                raise ValueError(
                    "Each changed file must have a valid filename."
                )

            patch = changed_file.get("patch", "")

            # GitHub may omit patches for binary files or large diffs.
            if not isinstance(patch, str):
                raise ValueError(
                    "The file patch must be a string."
                )

            added_lines = [
                line[1:]
                for line in patch.splitlines()
                if line.startswith("+") and not line.startswith("+++")
            ]

            for line in added_lines:

                for rule in self.RULES:

                    if rule["pattern"].search(line):

                        findings.append(
                            AgentFinding(
                                title=rule["title"],
                                description=rule["description"],
                                severity=rule["severity"],
                                category=rule["category"],
                                file_path=file_path,
                                recommendation=rule["recommendation"],
                            )
                        )

        overall_risk = self._calculate_risk(findings)

        summary = (
            f"Reviewed {len(changed_files)} changed files "
            f"and identified {len(findings)} potential issues."
        )

        recommendations = list(
            dict.fromkeys(
                finding.recommendation
                for finding in findings
                if finding.recommendation
            )
        )

        if not findings:
            recommendations.append(
                "No configured pattern-based issues were detected. "
                "Manual review and testing are still required."
            )

        return CodeReviewResult(
            summary=summary,
            findings=findings,
            overall_risk=overall_risk,
            recommendations=recommendations,
        )

    @staticmethod
    def _calculate_risk(findings):

        severity_order = {
            FindingSeverity.INFO: 0,
            FindingSeverity.LOW: 1,
            FindingSeverity.MEDIUM: 2,
            FindingSeverity.HIGH: 3,
            FindingSeverity.CRITICAL: 4,
        }

        if not findings:
            return FindingSeverity.INFO

        return max(
            (finding.severity for finding in findings),
            key=lambda severity: severity_order[severity],
        )