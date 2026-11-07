import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


DEFAULT_KEY_LABEL = "api-key"


@dataclass(frozen=True)
class AuthSettings:
    """Resolved authentication configuration (secrets never logged)."""

    api_keys: tuple[str, ...]
    key_labels: tuple[str, ...]
    environment: str

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_configured(self) -> bool:
        return len(self.api_keys) > 0


def _parse_csv(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ()

    return tuple(
        part.strip()
        for part in raw.split(",")
        if part.strip()
    )


def get_auth_settings() -> AuthSettings:
    """
    Load auth settings from the environment.

    DOCU_MIND_API_KEYS: comma-separated API key secrets
    DOCU_MIND_API_KEY_NAMES: optional comma-separated labels (same order)
    DOCU_MIND_ENV: production|development — unset means production
    """

    api_keys = _parse_csv(os.getenv("DOCU_MIND_API_KEYS"))
    key_labels = _parse_csv(os.getenv("DOCU_MIND_API_KEY_NAMES"))

    env_raw = os.getenv("DOCU_MIND_ENV")
    if env_raw is None or not env_raw.strip():
        environment = "production"
    else:
        environment = env_raw.strip().lower()

    return AuthSettings(
        api_keys=api_keys,
        key_labels=key_labels,
        environment=environment,
    )


def label_for_key_index(settings: AuthSettings, index: int) -> str:
    if 0 <= index < len(settings.key_labels):
        label = settings.key_labels[index].strip()
        if label:
            return label

    return DEFAULT_KEY_LABEL
