import httpx

from fastapi import APIRouter, HTTPException, Query

from backend.app.services.github_service import GitHubService


# --------------------------------------------------
# Router Configuration
# --------------------------------------------------

router = APIRouter(
    prefix="/api/v1/github",
    tags=["GitHub Integration"]
)

github_service = GitHubService()


# --------------------------------------------------
# GitHub Error Handler
# --------------------------------------------------

def handle_github_http_error(
    error: httpx.HTTPStatusError
) -> HTTPException:
    """
    Convert GitHub API errors into safe,
    meaningful HTTP responses.
    """

    response = error.response

    status_code = response.status_code

    error_message = str(error).lower()

    # ----------------------------------------------
    # Handle GitHub Rate Limit Errors
    # ----------------------------------------------

    if (
        status_code == 429
        or "rate limit exceeded" in error_message
    ):

        detail = {
            "message": "GitHub API rate limit exceeded.",
            "retry_after": response.headers.get(
                "Retry-After"
            ),
            "rate_limit_reset_at": response.headers.get(
                "X-RateLimit-Reset"
            )
        }

        return HTTPException(
            status_code=status_code,
            detail=detail
        )

    # ----------------------------------------------
    # Handle Other GitHub HTTP Errors
    # ----------------------------------------------

    return HTTPException(
        status_code=status_code,
        detail={
            "message": "GitHub API request failed."
        }
    )


# --------------------------------------------------
# 1. Get Repository Information
# --------------------------------------------------

@router.get("/repositories/{owner}/{repo}")
async def analyze_repository(
    owner: str,
    repo: str
):
    """
    Retrieve GitHub repository information.
    """

    try:

        return await github_service.get_repository(
            owner,
            repo
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except httpx.HTTPStatusError as error:

        raise handle_github_http_error(
            error
        ) from error

    except httpx.RequestError as error:

        raise HTTPException(
            status_code=502,
            detail="Unable to connect to GitHub."
        ) from error


# --------------------------------------------------
# 2. Get Repository Commits
# --------------------------------------------------

@router.get("/repositories/{owner}/{repo}/commits")
async def analyze_commits(
    owner: str,
    repo: str,
    per_page: int = Query(
        default=10,
        ge=1,
        le=100
    ),
    page: int = Query(
        default=1,
        ge=1
    )
):
    """
    Retrieve repository commits with pagination.
    """

    try:

        return await github_service.get_commits(
            owner=owner,
            repo=repo,
            per_page=per_page,
            page=page
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except httpx.HTTPStatusError as error:

        raise handle_github_http_error(
            error
        ) from error

    except httpx.RequestError as error:

        raise HTTPException(
            status_code=502,
            detail="Unable to connect to GitHub."
        ) from error


# --------------------------------------------------
# 3. Get Pull Request and Changed Files
# --------------------------------------------------

@router.get(
    "/repositories/{owner}/{repo}/pulls/{pull_number}"
)
async def analyze_pull_request(
    owner: str,
    repo: str,
    pull_number: int,
    per_page: int = Query(
        default=30,
        ge=1,
        le=100
    ),
    page: int = Query(
        default=1,
        ge=1
    )
):
    """
    Retrieve pull request details and changed files.
    """

    try:

        # Retrieve pull request details.
        pull_request = (
            await github_service.get_pull_request(
                owner,
                repo,
                pull_number
            )
        )

        # Retrieve changed files.
        changed_files = (
            await github_service.get_pull_request_files(
                owner=owner,
                repo=repo,
                pull_number=pull_number,
                per_page=per_page,
                page=page
            )
        )

        return {
            "pull_request": pull_request,
            "changed_files": changed_files
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except httpx.HTTPStatusError as error:

        raise handle_github_http_error(
            error
        ) from error

    except httpx.RequestError as error:

        raise HTTPException(
            status_code=502,
            detail="Unable to connect to GitHub."
        ) from error