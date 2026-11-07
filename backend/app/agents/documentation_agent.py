from typing import Any

from pydantic import BaseModel

from backend.app.agents.base_agent import BaseAgent
from backend.app.schemas.agent import (
    AgentInput,
    AgentName,
    DocumentationResult,
)


class DocumentationAgent(BaseAgent):
    """
    Generates deterministic technical documentation from repository,
    commit, and GitHub pull-request information.

    Supports both filename strings and GitHub changed-file objects.
    Extracts additions and deletions from available unified diffs.

    This implementation does not use an LLM. Its summaries and impact
    assessments are based only on the supplied repository information.
    """

    agent_name = AgentName.DOCUMENTATION

    MAX_DISPLAYED_LINES = 8
    MAX_LINE_LENGTH = 180

    async def execute(
        self,
        agent_input: AgentInput,
    ) -> BaseModel:

        context = agent_input.context

        repository = context.get(
            "repository",
            "Unknown repository",
        )

        if not isinstance(repository, str):
            raise ValueError("repository must be a string.")

        commits = context.get("commits", [])
        changed_files = context.get("changed_files", [])

        if not isinstance(commits, list):
            raise ValueError("commits must be a list.")

        if not isinstance(changed_files, list):
            raise ValueError("changed_files must be a list.")

        commit_messages = self._extract_commit_messages(commits)

        normalized_files = self._normalize_changed_files(changed_files)

        if not commit_messages and not normalized_files:
            raise ValueError(
                "Insufficient repository information for documentation."
            )

        summary = self._generate_summary(
            commit_messages,
            normalized_files,
        )

        markdown = self._generate_markdown(
            repository=repository,
            commit_messages=commit_messages,
            changed_files=normalized_files,
            summary=summary,
        )

        documentation_gaps = self._identify_gaps(normalized_files)

        if not commit_messages:
            documentation_gaps.append(
                "No commit messages were supplied. "
                "The documentation is based on changed-file information only."
            )

        return DocumentationResult(
            summary=summary,
            generated_markdown=markdown,
            files_covered=[
                item["filename"] for item in normalized_files
            ],
            documentation_gaps=documentation_gaps,
        )

    @staticmethod
    def _extract_commit_messages(commits: list[Any]) -> list[str]:

        messages = []

        for commit in commits:
            if not isinstance(commit, dict):
                raise ValueError("Each commit must be an object.")

            message = commit.get("message")

            if isinstance(message, str) and message.strip():
                messages.append(message.strip())

        return messages

    @staticmethod
    def _normalize_changed_files(
        changed_files: list[Any],
    ) -> list[dict[str, Any]]:

        normalized = []

        for changed_file in changed_files:

            # Backward compatibility with existing string-based input.
            if isinstance(changed_file, str):
                filename = changed_file.strip()

                if not filename:
                    raise ValueError("Changed file names cannot be empty.")

                normalized.append({
                    "filename": filename,
                    "status": "unknown",
                    "patch_available": False,
                    "additions": [],
                    "deletions": [],
                })

                continue

            if not isinstance(changed_file, dict):
                raise ValueError(
                    "Each changed file must be a filename or an object."
                )

            filename = changed_file.get("filename")

            if not isinstance(filename, str) or not filename.strip():
                raise ValueError(
                    "Each changed file object must contain a valid filename."
                )

            patch = changed_file.get("patch")

            if patch is not None and not isinstance(patch, str):
                raise ValueError(
                    "A changed file patch must be a string or None."
                )

            additions = []
            deletions = []

            if isinstance(patch, str):
                for line in patch.splitlines():

                    # Ignore unified diff headers and metadata.
                    if line.startswith("+++") or line.startswith("---"):
                        continue

                    if line.startswith("+"):
                        additions.append(line[1:])

                    elif line.startswith("-"):
                        deletions.append(line[1:])

            status = changed_file.get("status", "unknown")

            if not isinstance(status, str):
                raise ValueError("File status must be a string.")

            normalized.append({
                "filename": filename.strip(),
                "status": status,
                "patch_available": isinstance(patch, str),
                "additions": additions,
                "deletions": deletions,
            })

        return normalized

    @staticmethod
    def _generate_summary(
        commit_messages: list[str],
        changed_files: list[dict[str, Any]],
    ) -> str:

        file_count = len(changed_files)

        addition_count = sum(
            len(item["additions"]) for item in changed_files
        )

        deletion_count = sum(
            len(item["deletions"]) for item in changed_files
        )

        if commit_messages:
            change_description = "; ".join(commit_messages[:5])
        else:
            change_description = "No commit messages were provided."

        return (
            f"Analyzed {file_count} changed files, "
            f"identifying {addition_count} added lines and "
            f"{deletion_count} deleted lines in the available patches. "
            f"Commit information: {change_description}"
        )

    @staticmethod
    def _infer_impact(filename: str) -> str:

        normalized_path = filename.lower()

        if (
            "test" in normalized_path
            or "/tests/" in normalized_path
            or normalized_path.startswith("tests/")
        ):
            return (
                "This change is in a test-related file. "
                "It may affect test setup, assertions, or test execution. "
                "Run the relevant tests to verify the behavior."
            )

        if (
            normalized_path.endswith(".md")
            or normalized_path.endswith(".rst")
            or "/docs/" in normalized_path
        ):
            return (
                "This change appears documentation-related. "
                "Review the updated instructions and examples for accuracy."
            )

        if (
            "config" in normalized_path
            or normalized_path.endswith((".yaml", ".yml", ".toml", ".ini"))
        ):
            return (
                "This change appears configuration-related. "
                "Verify the affected settings in the target environment."
            )

        return (
            "This file contains code or other project content. "
            "The patch alone does not establish its complete runtime impact. "
            "Review surrounding code and run relevant tests."
        )

    @classmethod
    def _format_patch_lines(
        cls,
        lines: list[str],
        label: str,
    ) -> list[str]:

        if not lines:
            return [f"- No {label.lower()} lines identified in the supplied patch."]

        formatted = []

        for line in lines[:cls.MAX_DISPLAYED_LINES]:
            shortened = line[:cls.MAX_LINE_LENGTH]

            if len(line) > cls.MAX_LINE_LENGTH:
                shortened += "..."

            formatted.append(f"- `{shortened}`")

        remaining = len(lines) - cls.MAX_DISPLAYED_LINES

        if remaining > 0:
            formatted.append(
                f"- ...and {remaining} additional {label.lower()} lines."
            )

        return formatted

    @classmethod
    def _generate_markdown(
        cls,
        repository: str,
        commit_messages: list[str],
        changed_files: list[dict[str, Any]],
        summary: str,
    ) -> str:

        commit_section = "\n".join(
            f"- {message}" for message in commit_messages
        ) or "- No commit information available."

        file_sections = []

        for item in changed_files:

            filename = item["filename"]

            file_sections.extend([
                f"### `{filename}`",
                "",
                f"- Status: {item['status']}",
                f"- Added lines: {len(item['additions'])}",
                f"- Deleted lines: {len(item['deletions'])}",
                "",
                "**Added changes:**",
                *cls._format_patch_lines(item["additions"], "Added"),
                "",
                "**Deleted changes:**",
                *cls._format_patch_lines(item["deletions"], "Deleted"),
                "",
                "**Potential impact:**",
                cls._infer_impact(filename),
                "",
            ])

            if not item["patch_available"]:
                file_sections.append(
                    "> The GitHub patch was unavailable. "
                    "This section contains no line-level analysis."
                )
                file_sections.append("")

        changed_file_section = (
            "\n".join(file_sections)
            if file_sections
            else "No changed-file information available."
        )

        return f"""# Technical Change Documentation

## Repository

{repository}

## Summary

{summary}

## Commit History

{commit_section}

## Changed Files and Technical Analysis

{changed_file_section}

## Analysis Limitations

This report is generated using deterministic analysis of the supplied
repository metadata, commit messages, filenames, and available GitHub patches.

Potential impacts are preliminary observations, not verified runtime behavior.
No tests are claimed to have passed unless test execution results are supplied.

## Notes

This document was generated by the DocuMind AI Documentation Agent.
"""

    @staticmethod
    def _identify_gaps(
        changed_files: list[dict[str, Any]],
    ) -> list[str]:

        gaps = []

        has_readme = any(
            item["filename"].lower().endswith("readme.md")
            for item in changed_files
        )

        if not has_readme:
            gaps.append(
                "No README.md file was included in the supplied changes. "
                "This does not establish whether repository documentation "
                "already exists."
            )

        files_without_patches = [
            item["filename"]
            for item in changed_files
            if not item["patch_available"]
        ]

        if files_without_patches:
            gaps.append(
                "Patch content was unavailable for: "
                + ", ".join(files_without_patches)
                + ". Line-level analysis could not be performed for these files."
            )

        if not changed_files:
            gaps.append("No changed-file information was provided.")

        return gaps
