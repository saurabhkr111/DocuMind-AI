import os
import re

import httpx
from dotenv import load_dotenv


# Load environment variables from .env
load_dotenv()


# --------------------------------------------------
# GitHub Configuration
# --------------------------------------------------

GITHUB_API_BASE_URL = os.getenv(
    "GITHUB_API_BASE_URL",
    "https://api.github.com"
)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


class GitHubService:
    """
    Read-only GitHub REST API client for DocuMind AI.

    Features:
    - GitHub authentication
    - Repository information retrieval
    - Commit retrieval with pagination
    - Pull request retrieval
    - Pull request files retrieval with pagination
    - Repository input validation
    - Primary rate-limit detection
    - Secondary rate-limit detection
    - HTTP error handling
    """

    def __init__(self):
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        if GITHUB_TOKEN:
            self.headers["Authorization"] = (
                f"Bearer {GITHUB_TOKEN}"
            )

    # --------------------------------------------------
    # Repository Validation
    # --------------------------------------------------

    @staticmethod
    def validate_repository(owner: str, repo: str):
        """
        Validate GitHub owner and repository identifiers.
        """

        pattern = (
            r"^[A-Za-z0-9]"
            r"(?:[A-Za-z0-9-]*[A-Za-z0-9])?$"
        )

        if not re.fullmatch(pattern, owner):
            raise ValueError(
                "Invalid GitHub owner name."
            )

        if not re.fullmatch(pattern, repo):
            raise ValueError(
                "Invalid GitHub repository name."
            )

    # --------------------------------------------------
    # GitHub API GET Request
    # --------------------------------------------------

    async def _get(self, endpoint: str, params=None):
        """
        Perform a read-only GET request to GitHub.

        Handles:
        - Primary rate limits
        - Secondary rate limits
        - HTTP 429 responses
        - Other HTTP errors
        """

        url = f"{GITHUB_API_BASE_URL}{endpoint}"

        async with httpx.AsyncClient(
            timeout=20.0
        ) as client:

            response = await client.get(
                url,
                headers=self.headers,
                params=params
            )

        # ----------------------------------------------
        # GitHub Rate Limit Detection
        # ----------------------------------------------

        if response.status_code in (403, 429):

            remaining = response.headers.get(
                "X-RateLimit-Remaining"
            )

            reset_time = response.headers.get(
                "X-RateLimit-Reset"
            )

            retry_after = response.headers.get(
                "Retry-After"
            )

            # Read GitHub's error message safely.
            try:
                error_data = response.json()

            except ValueError:
                error_data = {}

            api_message = ""

            if isinstance(error_data, dict):

                message = error_data.get(
                    "message",
                    ""
                )

                if isinstance(message, str):
                    api_message = message

            api_message_lower = api_message.lower()

            # Detect primary and secondary rate limits.
            is_rate_limited = (
                response.status_code == 429
                or remaining == "0"
                or retry_after is not None
                or "rate limit" in api_message_lower
            )

            if is_rate_limited:

                error_message = (
                    "GitHub API rate limit exceeded."
                )

                # Retry-After can be seconds or an HTTP date.
                if retry_after:
                    if retry_after.isdigit():
                        error_message += (
                            f" Retry after {retry_after} seconds."
                        )
                    else:
                        error_message += (
                            f" Retry after: {retry_after}."
                    )
                if reset_time:
                    error_message += (
                        " Primary rate limit resets at "
                        f"Unix timestamp {reset_time}."
                    )

                raise httpx.HTTPStatusError(
                    error_message,
                    request=response.request,
                    response=response
                )

        # ----------------------------------------------
        # Handle Other HTTP Errors
        # ----------------------------------------------

        response.raise_for_status()

        return response.json()

    # --------------------------------------------------
    # Repository Information
    # --------------------------------------------------

    async def get_repository(
        self,
        owner: str,
        repo: str
    ):
        """
        Retrieve GitHub repository information.
        """

        self.validate_repository(owner, repo)

        return await self._get(
            f"/repos/{owner}/{repo}"
        )

    # --------------------------------------------------
    # Repository Commits
    # --------------------------------------------------

    async def get_commits(
        self,
        owner: str,
        repo: str,
        per_page: int = 10,
        page: int = 1
    ):
        """
        Retrieve a specific page of repository commits.
        """

        self.validate_repository(owner, repo)

        if not 1 <= per_page <= 100:
            raise ValueError(
                "per_page must be between 1 and 100."
            )

        if page < 1:
            raise ValueError(
                "page must be greater than or equal to 1."
            )

        return await self._get(
            f"/repos/{owner}/{repo}/commits",
            params={
                "per_page": per_page,
                "page": page
            }
        )

    # --------------------------------------------------
    # Pull Request Information
    # --------------------------------------------------

    async def get_pull_request(
        self,
        owner: str,
        repo: str,
        pull_number: int
    ):
        """
        Retrieve pull request information.
        """

        self.validate_repository(owner, repo)

        if pull_number < 1:
            raise ValueError(
                "Pull request number must be positive."
            )

        return await self._get(
            f"/repos/{owner}/{repo}/pulls/{pull_number}"
        )

    # --------------------------------------------------
    # Pull Request Changed Files
    # --------------------------------------------------

    async def get_pull_request_files(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        per_page: int = 30,
        page: int = 1
    ):
        """
        Retrieve a specific page of changed files
        from a pull request.
        """

        self.validate_repository(owner, repo)

        if pull_number < 1:
            raise ValueError(
                "Pull request number must be positive."
            )

        if not 1 <= per_page <= 100:
            raise ValueError(
                "per_page must be between 1 and 100."
            )

        if page < 1:
            raise ValueError(
                "page must be greater than or equal to 1."
            )

        return await self._get(
            f"/repos/{owner}/{repo}/pulls/{pull_number}/files",
            params={
                "per_page": per_page,
                "page": page
            }
        )