import hmac
from typing import Annotated

from fastapi import Header, HTTPException, status

from backend.app.auth.config import get_auth_settings, label_for_key_index
from backend.app.auth.principal import Principal


def _extract_bearer_token(authorization: str | None) -> str | None:
    if authorization is None:
        return None

    scheme, _, credentials = authorization.partition(" ")

    if scheme.lower() != "bearer" or not credentials.strip():
        return None

    # Reject extra whitespace-only or multi-token ambiguity after first space
    # by requiring a non-empty token; further spaces are part of the token.
    return credentials.strip()


def get_current_principal(
    authorization: Annotated[str | None, Header()] = None,
) -> Principal:
    """
    Require a valid Authorization: Bearer <api-key> header.

    Returns 401 for missing, malformed, or invalid credentials.
    Returns 503 when no API keys are configured (fail closed).
    """

    settings = get_auth_settings()

    if not settings.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured.",
        )

    token = _extract_bearer_token(authorization)

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    matched_index: int | None = None

    for index, configured_key in enumerate(settings.api_keys):
        # compare_digest requires equal length; unequal length is a non-match.
        if len(token) != len(configured_key):
            continue

        if hmac.compare_digest(token, configured_key):
            matched_index = index
            break

    if matched_index is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Principal(
        name=label_for_key_index(settings, matched_index)
    )
