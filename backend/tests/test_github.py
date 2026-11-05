import httpx
import pytest

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.routes.github import github_service

client = TestClient(app)


def test_repository_success(monkeypatch):

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


def test_commits_success(monkeypatch):

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


def test_pull_request_success(monkeypatch):

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


def test_pull_request_pagination_parameters(monkeypatch):

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
def test_invalid_pull_request_pagination(query):

    response = client.get(
        f"/api/v1/github/repositories/octocat/Hello-World/pulls/1{query}"
    )

    assert response.status_code == 422


def test_invalid_repository_owner():

    response = client.get(
        "/api/v1/github/repositories/invalid_owner/Hello-World"
    )

    assert response.status_code == 400


def test_invalid_commits_per_page():

    response = client.get(
        "/api/v1/github/repositories/octocat/Hello-World/commits?per_page=200"
    )

    assert response.status_code == 422


def test_nonexistent_repository(monkeypatch):

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


def test_github_network_error(monkeypatch):

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