import pytest
from pydantic import ValidationError

from app.core.config import PLACEHOLDER_SECRET_KEY, Settings


def test_backend_cors_origins_accepts_csv(monkeypatch) -> None:
    monkeypatch.setenv(
        "BACKEND_CORS_ORIGINS",
        "http://localhost:5173, https://fridgestare.example",
    )

    settings = Settings(_env_file=None)

    assert settings.backend_cors_origins == [
        "http://localhost:5173",
        "https://fridgestare.example",
    ]


def test_backend_cors_origins_accepts_json_array(monkeypatch) -> None:
    monkeypatch.setenv(
        "BACKEND_CORS_ORIGINS",
        '["http://localhost:5173", "https://fridgestare.example"]',
    )

    settings = Settings(_env_file=None)

    assert settings.backend_cors_origins == [
        "http://localhost:5173",
        "https://fridgestare.example",
    ]


def production_env(monkeypatch, **overrides: str) -> None:
    """A minimally valid production environment, before the test breaks one thing."""
    defaults = {
        "APP_ENV": "production",
        "APP_SECRET_KEY": "k" * 48,
        "APP_BASE_URL": "https://fridgestare.example",
        "COOKIE_SECURE": "true",
        "SCHEDULER_ENABLED": "false",
        "MAILGUN_API_KEY": "",
        "MAILGUN_DOMAIN": "",
        "MAIL_FROM_ADDRESS": "plans@fridgestare.example",
    }
    for key, value in {**defaults, **overrides}.items():
        monkeypatch.setenv(key, value)


def test_valid_production_settings_load(monkeypatch) -> None:
    production_env(monkeypatch)

    settings = Settings(_env_file=None)

    assert settings.is_production is True
    # Docs default off in production so a single-user app does not advertise its API.
    assert settings.docs_url is None
    assert settings.openapi_url is None


def test_production_rejects_the_placeholder_secret_key(monkeypatch) -> None:
    production_env(monkeypatch, APP_SECRET_KEY=PLACEHOLDER_SECRET_KEY)

    with pytest.raises(ValidationError, match="APP_SECRET_KEY is still the example placeholder"):
        Settings(_env_file=None)


def test_production_rejects_a_short_secret_key(monkeypatch) -> None:
    production_env(monkeypatch, APP_SECRET_KEY="too-short")

    with pytest.raises(ValidationError, match="at least 32 characters"):
        Settings(_env_file=None)


def test_production_requires_secure_cookies_over_https(monkeypatch) -> None:
    production_env(monkeypatch, COOKIE_SECURE="false")

    with pytest.raises(ValidationError, match="COOKIE_SECURE must be true"):
        Settings(_env_file=None)


def test_production_requires_an_https_base_url(monkeypatch) -> None:
    production_env(monkeypatch, APP_BASE_URL="http://fridgestare.example")

    with pytest.raises(ValidationError, match="APP_BASE_URL must be an https URL"):
        Settings(_env_file=None)


def test_production_scheduler_requires_mailgun(monkeypatch) -> None:
    production_env(monkeypatch, SCHEDULER_ENABLED="true")

    with pytest.raises(ValidationError, match="Mailgun is not configured"):
        Settings(_env_file=None)


def test_production_rejects_the_placeholder_sender_address(monkeypatch) -> None:
    production_env(
        monkeypatch,
        MAILGUN_API_KEY="key-123",
        MAILGUN_DOMAIN="mg.fridgestare.example",
        MAIL_FROM_ADDRESS="hello@fridgestare.local",
    )

    message = r"MAIL_FROM_ADDRESS is still the \.local placeholder"
    with pytest.raises(ValidationError, match=message):
        Settings(_env_file=None)


def test_development_keeps_permissive_defaults(monkeypatch) -> None:
    monkeypatch.setenv("APP_SECRET_KEY", PLACEHOLDER_SECRET_KEY)

    settings = Settings(_env_file=None)

    assert settings.is_production is False
    assert settings.docs_url == "/docs"
