import pytest

from backend.app.auth import Principal, get_current_principal
from backend.app.main import app


# Display name used by document approval assertions in existing suites.
TEST_PRINCIPAL = Principal(name="Project Admin")


def apply_test_auth_override() -> None:
    """Bypass real API-key checks for HTTP suites that exercise business logic."""

    app.dependency_overrides[get_current_principal] = (
        lambda: TEST_PRINCIPAL
    )


def clear_test_auth_override() -> None:
    app.dependency_overrides.pop(get_current_principal, None)


@pytest.fixture
def test_principal() -> Principal:
    return TEST_PRINCIPAL
