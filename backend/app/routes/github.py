from fastapi import APIRouter, HTTPException, Query
import httpx

from backend.app.services.github_service import GitHubService

router = APIRouter(
    prefix="/api/v1/github",
    tags=["GitHub Integration"]
)

github_service = GitHubService()


@router.get("/repositories/{owner}/{repo}")
async def analyze_repository(owner: str, repo: str):
    """Retrieve GitHub repository information."""

    try:
        return await github_service.get_repository(owner, repo)

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=error.response.status_code,
            detail="GitHub API request failed."
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to GitHub."
        )


@router.get("/repositories/{owner}/{repo}/commits")
async def analyze_commits(
    owner: str,
    repo: str,
    per_page: int = Query(default=10, ge=1, le=100),
    page: int = Query(default=1, ge=1)
):
    """Retrieve a specific page of repository commits."""

    try:
        return await github_service.get_commits(
            owner=owner,
            repo=repo,
            per_page=per_page,
            page=page
        )

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=error.response.status_code,
            detail="GitHub API request failed."
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to GitHub."
        )


@router.get(
    "/repositories/{owner}/{repo}/pulls/{pull_number}"
)
async def analyze_pull_request(
    owner: str,
    repo: str,
    pull_number: int
):
    """Retrieve PR details and changed files."""

    try:
        pull_request = await github_service.get_pull_request(
            owner, repo, pull_number
        )

        changed_files = await github_service.get_pull_request_files(
            owner, repo, pull_number
        )

        return {
            "pull_request": pull_request,
            "changed_files": changed_files
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=error.response.status_code,
            detail="GitHub API request failed."
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to GitHub."
        )