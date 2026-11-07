import httpx

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.auth import Principal, get_current_principal
from backend.app.services.github_service import GitHubService

from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.orchestrator.agent_orchestrator import AgentOrchestrator
from backend.app.schemas.agent import AgentInput, AgentStatus
from backend.app.services.agent_persistence_service import (
    persist_agent_results,
)

#github_service = GitHubService()

# --------------------------------------------------
# Router Configuration
# --------------------------------------------------

router = APIRouter(
    prefix="/api/v1/github",
    tags=["GitHub Integration"]
)

github_service = GitHubService()
orchestrator = AgentOrchestrator()


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
    repo: str,
    principal: Principal = Depends(get_current_principal),
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
    ),
    principal: Principal = Depends(get_current_principal),
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
    ),
    principal: Principal = Depends(get_current_principal),
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

# --------------------------------------------------
# 4. Analyze GitHub Pull Request with DocuMind AI
# --------------------------------------------------

@router.post(
    "/repositories/{owner}/{repo}/pulls/{pull_number}/analyze"
)
async def analyze_pull_request_with_documind(
    owner: str,
    repo: str,
    pull_number: int,
    per_page: int = Query(default=30, ge=1, le=100),
    page: int = Query(default=1, ge=1),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    """
    Fetch a GitHub PR, execute all three DocuMind agents,
    and persist the workflow and generated documentation.
    """

    try:
        # 1. Fetch Pull Request information.
        pull_request = await github_service.get_pull_request(
            owner,
            repo,
            pull_number,
        )

        # 2. Fetch changed files and patches.
        changed_files = await github_service.get_pull_request_files(
            owner=owner,
            repo=repo,
            pull_number=pull_number,
            per_page=per_page,
            page=page,
        )

        if not changed_files:
            raise HTTPException(
                status_code=422,
                detail="This Pull Request contains no changed files.",
            )

        # 3. Prepare repository context.
        repository_name = f"{owner}/{repo}"

        pr_url = pull_request.get(
            "html_url",
            f"https://github.com/{owner}/{repo}/pull/{pull_number}",
        )

        agent_input = AgentInput(
            task=(
                f"Analyze GitHub Pull Request #{pull_number}: "
                f"{pull_request.get('title', 'Untitled PR')}. "
                f"Review the changed files, identify code issues, "
                f"generate technical documentation, and summarize "
                f"team actions."
            ),
            source_type="github_pull_request",
            source_reference=pr_url,
            context={
                "repository": repository_name,
                "pull_request": pull_request,
                "commits": [],
                "changed_files": changed_files,
            },
        )

        # 4. Execute Documentation, Code Review,
        #    and Team Intelligence agents.
        results = await orchestrator.run(agent_input)

        # 5. Persist workflow, agent logs, and documentation.
        workflow = persist_agent_results(
            db=db,
            agent_input=agent_input,
            results=results,
        )

        # 6. Check agent execution status.
        if not results or all(
            result.status == AgentStatus.FAILED
            for result in results.values()
        ):
            raise HTTPException(
                status_code=500,
                detail="All DocuMind agents failed.",
            )

        # 7. Return complete analysis.
        return {
            "message": "GitHub Pull Request analyzed successfully.",
            "repository": repository_name,
            "pull_request": pull_request,
            "workflow_id": workflow.id,
            "workflow_status": workflow.status,
            "agent_results": results,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except httpx.HTTPStatusError as error:
        raise handle_github_http_error(error) from error

    except httpx.RequestError as error:
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to GitHub.",
        ) from error

    except HTTPException:
        raise

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="GitHub PR analysis or workflow persistence failed.",
        ) from error
    