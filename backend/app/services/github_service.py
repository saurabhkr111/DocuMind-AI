import os
import re

import httpx
from dotenv import load_dotenv

load_dotenv()

GITHUB_API_BASE_URL = os.getenv(
    "GITHUB_API_BASE_URL",
    "https://api.github.com"
)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


class GitHubService:
    """Read-only GitHub REST API client for DocuMind AI."""

    def __init__(self):
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        if GITHUB_TOKEN:
            self.headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    @staticmethod
    def validate_repository(owner: str, repo: str):
        """Validate GitHub owner and repository identifiers."""

        pattern = r"^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?$"

        if not re.fullmatch(pattern, owner):
            raise ValueError("Invalid GitHub owner name.")

        if not re.fullmatch(pattern, repo):
            raise ValueError("Invalid GitHub repository name.")

    async def _get(self, endpoint: str, params=None):
        """Perform a read-only GET request to GitHub."""

        url = f"{GITHUB_API_BASE_URL}{endpoint}"

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                url,
                headers=self.headers,
                params=params
            )

        response.raise_for_status()
        return response.json()

    async def get_repository(self, owner: str, repo: str):
        self.validate_repository(owner, repo)

        return await self._get(f"/repos/{owner}/{repo}")

    async def get_commits(
        self,
        owner: str,
        repo: str,
        per_page: int = 10
    ):
        self.validate_repository(owner, repo)

        if not 1 <= per_page <= 100:
            raise ValueError("per_page must be between 1 and 100.")

        return await self._get(
            f"/repos/{owner}/{repo}/commits",
            params={"per_page": per_page}
        )

    async def get_pull_request(
        self,
        owner: str,
        repo: str,
        pull_number: int
    ):
        self.validate_repository(owner, repo)

        if pull_number < 1:
            raise ValueError("Pull request number must be positive.")

        return await self._get(
            f"/repos/{owner}/{repo}/pulls/{pull_number}"
        )

    async def get_pull_request_files(
        self,
        owner: str,
        repo: str,
        pull_number: int
    ):
        self.validate_repository(owner, repo)

        if pull_number < 1:
            raise ValueError("Pull request number must be positive.")

        return await self._get(
            f"/repos/{owner}/{repo}/pulls/{pull_number}/files"
        )