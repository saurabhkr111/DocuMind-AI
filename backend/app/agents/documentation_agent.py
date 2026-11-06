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
    Generates technical documentation from repository,
    commit, and pull-request information.

    Initial implementation uses deterministic logic.
    LLM integration will be added later.
    """

    agent_name = AgentName.DOCUMENTATION

    async def execute(
        self,
        agent_input: AgentInput
    ) -> BaseModel:

        context = agent_input.context

        repository = context.get(
            "repository",
            "Unknown repository"
        )

        commits = context.get("commits", [])

        changed_files = context.get(
            "changed_files",
            []
        )

        if not isinstance(commits, list):
            raise ValueError("commits must be a list.")

        if not isinstance(changed_files, list):
            raise ValueError("changed_files must be a list.")

        commit_messages = []

        for commit in commits:
            if not isinstance(commit, dict):
                raise ValueError("Each commit must be an object.")

            message = commit.get("message")

            if isinstance(message, str) and message.strip():
                commit_messages.append(message.strip())

        if not commit_messages and not changed_files:
            raise ValueError(
                "Insufficient repository information for documentation."
            )

        summary = self._generate_summary(
            commit_messages,
            changed_files
        )

        markdown = self._generate_markdown(
            repository,
            commit_messages,
            changed_files,
            summary
        )

        documentation_gaps = self._identify_gaps(
            changed_files
        )

        return DocumentationResult(
            summary=summary,
            generated_markdown=markdown,
            files_covered=changed_files,
            documentation_gaps=documentation_gaps,
        )

    @staticmethod
    def _generate_summary(
        commit_messages: list[str],
        changed_files: list[str]
    ) -> str:

        if commit_messages:
            changes = "; ".join(commit_messages[:5])
        else:
            changes = "No commit messages were provided."

        return (
            f"Analyzed {len(changed_files)} changed files. "
            f"Changes include: {changes}"
        )

    @staticmethod
    def _generate_markdown(
        repository: str,
        commit_messages: list[str],
        changed_files: list[str],
        summary: str
    ) -> str:

        commit_section = "\n".join(
            f"- {message}"
            for message in commit_messages
        ) or "- No commit information available."

        file_section = "\n".join(
            f"- `{file_path}`"
            for file_path in changed_files
        ) or "- No changed files available."

        return f"""# Technical Change Documentation

## Repository

{repository}

## Summary

{summary}

## Commit History

{commit_section}

## Changed Files

{file_section}

## Notes

This document was generated from the repository
information supplied to the Documentation Agent.
"""

    @staticmethod
    def _identify_gaps(
        changed_files: list[str]
    ) -> list[str]:

        gaps = []

        has_readme = any(
            path.lower().endswith("readme.md")
            for path in changed_files
        )

        if not has_readme:
            gaps.append(
                "No README.md file was included in the supplied changes. "
                "This does not establish whether repository documentation "
                "already exists."
            )

        if not changed_files:
            gaps.append(
                "No changed-file information was provided."
            )

        return gaps