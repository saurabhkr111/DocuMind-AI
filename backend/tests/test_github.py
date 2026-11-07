import asyncio
import httpx
import pytest

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.routes.github import github_service
from backend.tests.conftest import apply_test_auth_override


@pytest.fixture
def client():
    previous_overrides = app.dependency_overrides.copy()
    apply_test_auth_override()

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


def test_repository_success(client, monkeypatch):

    async def mock_get_repository(owner, repo):
        return {
            "full_name": f"{owner}/{repo}",
            "private": False,
            "stargazers_count": 100
        }

    monkeypatch.setattr(
        github_service,
        "get_repository",
        mock_get_repository
    )

    response = client.get(
        "/api/v1/github/repositories/octocat/Hello-World"
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "octocat/Hello-World"


def test_commits_success(client, monkeypatch):

    async def mock_get_commits(
        owner,
        repo,
        per_page=10,
        page=1
    ):
        return [
            {
                "sha": "abc123",
                "commit": {
                    "message": "Initial commit"
                }
            }
        ]

    monkeypatch.setattr(
        github_service,
        "get_commits",
        mock_get_commits
    )

    response = client.get(
        "/api/v1/github/repositories/octocat/Hello-World/commits?per_page=5"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["sha"] == "abc123"


def test_pull_request_success(client, monkeypatch):

    async def mock_get_pull_request(owner, repo, pull_number):
        return {
            "number": pull_number,
            "title": "Add documentation",
            "changed_files": [
                {
                    "filename": "README.md",
                    "status": "modified"
                }
            ]
        }

    async def mock_get_pull_request_files(
        owner,
        repo,
        pull_number,
        per_page=30,
        page=1
    ):
        return [
            {
                "filename": "README.md",
                "status": "modified",
                "additions": 5,
                "deletions": 1
            }
        ]

    monkeypatch.setattr(
        github_service,
        "get_pull_request",
        mock_get_pull_request
    )

    monkeypatch.setattr(
        github_service,
        "get_pull_request_files",
        mock_get_pull_request_files
    )

    response = client.get(
        "/api/v1/github/repositories/octocat/Hello-World/pulls/1"
    )

    assert response.status_code == 200
    assert response.json()["pull_request"]["number"] == 1
    assert response.json()["pull_request"]["title"] == "Add documentation"
    assert len(response.json()["changed_files"]) == 1
    assert response.json()["changed_files"][0]["filename"] == "README.md"


def test_pull_request_pagination_parameters(client, monkeypatch):

    captured_parameters = {}

    async def mock_get_pull_request(owner, repo, pull_number):
        return {
            "number": pull_number,
            "title": "Pagination test"
        }

    async def mock_get_pull_request_files(
        owner,
        repo,
        pull_number,
        per_page=30,
        page=1
    ):
        captured_parameters["per_page"] = per_page
        captured_parameters["page"] = page

        return [
            {
                "filename": "backend/main.py",
                "status": "modified"
            }
        ]

    monkeypatch.setattr(
        github_service,
        "get_pull_request",
        mock_get_pull_request
    )

    monkeypatch.setattr(
        github_service,
        "get_pull_request_files",
        mock_get_pull_request_files
    )

    response = client.get(
        "/api/v1/github/repositories/octocat/Hello-World/pulls/1?per_page=50&page=2"
    )

    assert response.status_code == 200
    assert captured_parameters["per_page"] == 50
    assert captured_parameters["page"] == 2


@pytest.mark.parametrize(
    "query",
    [
        "?per_page=200",
        "?per_page=0",
        "?page=0",
        "?page=-1"
    ]
)
def test_invalid_pull_request_pagination(client, query):

    response = client.get(
        f"/api/v1/github/repositories/octocat/Hello-World/pulls/1{query}"
    )

    assert response.status_code == 422


def test_invalid_repository_owner(client):

    response = client.get(
        "/api/v1/github/repositories/invalid_owner/Hello-World"
    )

    assert response.status_code == 400


def test_invalid_commits_per_page(client):

    response = client.get(
        "/api/v1/github/repositories/octocat/Hello-World/commits?per_page=200"
    )

    assert response.status_code == 422


def test_nonexistent_repository(client, monkeypatch):

    async def mock_get_repository(owner, repo):

        request = httpx.Request(
            "GET",
            "https://api.github.com/repos/test/missing"
        )

        response = httpx.Response(
            404,
            request=request
        )

        raise httpx.HTTPStatusError(
            "Repository not found",
            request=request,
            response=response
        )

    monkeypatch.setattr(
        github_service,
        "get_repository",
        mock_get_repository
    )

    response = client.get(
        "/api/v1/github/repositories/test/missing"
    )

    assert response.status_code == 404


def test_github_network_error(client, monkeypatch):

    async def mock_get_repository(owner, repo):

        request = httpx.Request(
            "GET",
            "https://api.github.com/repos/test/repo"
        )

        raise httpx.ConnectError(
            "Connection failed",
            request=request
        )

    monkeypatch.setattr(
        github_service,
        "get_repository",
        mock_get_repository
    )

    response = client.get(
        "/api/v1/github/repositories/test/repo"
    )

    assert response.status_code == 502

# --------------------------------------------------
# GitHub Rate Limit Tests
# --------------------------------------------------

def mock_github_response(
    monkeypatch,
    status_code,
    headers=None,
    body=None
):
    """
    Mock GitHub API responses for rate-limit testing.
    """

    request = httpx.Request(
        "GET",
        "https://api.github.com/repos/octocat/Hello-World"
    )

    response = httpx.Response(
        status_code=status_code,
        headers=headers or {},
        json=body or {},
        request=request
    )

    class MockAsyncClient:

        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(
            self,
            exc_type,
            exc_value,
            traceback
        ):
            pass

        async def get(
            self,
            url,
            headers=None,
            params=None
        ):
            return response

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        MockAsyncClient
    )

    return response


# --------------------------------------------------
# Test 1: Primary Rate Limit
# --------------------------------------------------

def test_primary_rate_limit(monkeypatch):

    mock_github_response(
        monkeypatch,
        status_code=403,
        headers={
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": "1794000000"
        },
        body={
            "message": "API rate limit exceeded."
        }
    )

    with pytest.raises(
        httpx.HTTPStatusError
    ) as error:

        asyncio.run(
            github_service._get(
                "/repos/octocat/Hello-World"
            )
        )

    assert error.value.response.status_code == 403

    assert "rate limit exceeded" in str(
        error.value
    ).lower()


# --------------------------------------------------
# Test 2: Secondary Rate Limit
# --------------------------------------------------

def test_secondary_rate_limit(monkeypatch):

    mock_github_response(
        monkeypatch,
        status_code=403,
        headers={
            "X-RateLimit-Remaining": "50"
        },
        body={
            "message": (
                "You have exceeded a secondary rate limit."
            )
        }
    )

    with pytest.raises(
        httpx.HTTPStatusError
    ) as error:

        asyncio.run(
            github_service._get(
                "/repos/octocat/Hello-World"
            )
        )

    assert error.value.response.status_code == 403

    assert "rate limit exceeded" in str(
        error.value
    ).lower()


# --------------------------------------------------
# Test 3: HTTP 429 Rate Limit
# --------------------------------------------------

def test_http_429_rate_limit(monkeypatch):

    mock_github_response(
        monkeypatch,
        status_code=429,
        headers={
            "Retry-After": "60"
        },
        body={
            "message": "Too many requests."
        }
    )

    with pytest.raises(
        httpx.HTTPStatusError
    ) as error:

        asyncio.run(
            github_service._get(
                "/repos/octocat/Hello-World"
            )
        )

    assert error.value.response.status_code == 429

    assert "rate limit exceeded" in str(
        error.value
    ).lower()

    assert "60 seconds" in str(
        error.value
    )


# --------------------------------------------------
# Test 4: Normal HTTP 403 Error
# --------------------------------------------------

def test_normal_403_error(monkeypatch):

    mock_github_response(
        monkeypatch,
        status_code=403,
        headers={
            "X-RateLimit-Remaining": "50"
        },
        body={
            "message": (
                "Resource not accessible by integration."
            )
        }
    )

    with pytest.raises(
        httpx.HTTPStatusError
    ) as error:

        asyncio.run(
            github_service._get(
                "/repos/octocat/Hello-World"
            )
        )

    assert error.value.response.status_code == 403

    assert "rate limit exceeded" not in str(
        error.value
    ).lower()

# --------------------------------------------------
# GitHub Route-Level Error Handling Tests
# --------------------------------------------------


def create_github_http_error(
    status_code,
    message,
    headers=None
):
    """Create a mock GitHub HTTPStatusError."""

    request = httpx.Request(
        "GET",
        "https://api.github.com/repos/octocat/Hello-World"
    )

    response = httpx.Response(
        status_code=status_code,
        headers=headers or {},
        json={"message": message},
        request=request
    )

    return httpx.HTTPStatusError(
        "GitHub API rate limit exceeded."
        if "rate limit" in message.lower()
        else "GitHub API request failed.",
        request=request,
        response=response
    )


def test_repository_primary_rate_limit_route(client, monkeypatch):
    """Verify structured primary rate-limit response."""

    async def mock_get_repository(owner, repo):
        raise create_github_http_error(
            status_code=403,
            message="API rate limit exceeded.",
            headers={
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": "1794000000"
            }
        )

    monkeypatch.setattr(
        github_service,
        "get_repository",
        mock_get_repository
    )

    response = client.get(
        "/api/v1/github/repositories/octocat/Hello-World"
    )

    assert response.status_code == 403

    detail = response.json()["detail"]

    assert detail["message"] == "GitHub API rate limit exceeded."
    assert detail["rate_limit_reset_at"] == "1794000000"


def test_commits_secondary_rate_limit_route(client, monkeypatch):
    """Verify structured secondary rate-limit response."""

    async def mock_get_commits(
        owner,
        repo,
        per_page=10,
        page=1
    ):
        raise create_github_http_error(
            status_code=403,
            message="You have exceeded a secondary rate limit."
        )

    monkeypatch.setattr(
        github_service,
        "get_commits",
        mock_get_commits
    )

    response = client.get(
        "/api/v1/github/repositories/octocat/Hello-World/commits"
    )

    assert response.status_code == 403

    detail = response.json()["detail"]

    assert detail["message"] == "GitHub API rate limit exceeded."


def test_pull_request_http_429_rate_limit_route(client, monkeypatch):
    """Verify HTTP 429 response and retry information."""

    async def mock_get_pull_request(
        owner,
        repo,
        pull_number
    ):
        raise create_github_http_error(
            status_code=429,
            message="Too many requests.",
            headers={
                "Retry-After": "60"
            }
        )

    monkeypatch.setattr(
        github_service,
        "get_pull_request",
        mock_get_pull_request
    )

    response = client.get(
        "/api/v1/github/repositories/octocat/Hello-World/pulls/1"
    )

    assert response.status_code == 429

    detail = response.json()["detail"]

    assert detail["message"] == "GitHub API rate limit exceeded."
    assert detail["retry_after"] == "60"


def test_repository_normal_403_route(client, monkeypatch):
    """Verify normal 403 errors do not appear as rate limits."""

    async def mock_get_repository(owner, repo):
        raise create_github_http_error(
            status_code=403,
            message="Resource not accessible by integration."
        )

    monkeypatch.setattr(
        github_service,
        "get_repository",
        mock_get_repository
    )

    response = client.get(
        "/api/v1/github/repositories/octocat/Hello-World"
    )

    assert response.status_code == 403

    detail = response.json()["detail"]

    assert detail == {
        "message": "GitHub API request failed."
    }