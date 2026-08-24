import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]

# The placeholder shipped in .env.example. A deployment that keeps it is signing
# session cookies with a value published in this repository.
PLACEHOLDER_SECRET_KEY = "change-me-with-at-least-32-characters"
MINIMUM_SECRET_KEY_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env", ROOT_DIR / ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Fridgestare"
    api_prefix: str = "/api"
    # "production" turns on the startup checks in validate_deployment; anything else
    # keeps the permissive local defaults.
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = (
        "mysql+pymysql://fridgestare:fridgestare@localhost:3306/fridgestare?charset=utf8mb4"
    )
    app_secret_key: str = PLACEHOLDER_SECRET_KEY
    # Emails link to <app_base_url>/plans/<week>, which is an SPA route.
    app_base_url: AnyHttpUrl = "http://localhost:5173"
    access_token_expire_minutes: int = 60 * 24 * 7
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4.1-mini"
    tavily_api_key: str = ""
    mailgun_api_key: str = ""
    mailgun_domain: str = ""
    # Mailgun runs separate US and EU stacks; an EU sending domain needs
    # https://api.eu.mailgun.net or every send comes back 401.
    mailgun_base_url: str = "https://api.mailgun.net"
    mail_from_address: str = "hello@fridgestare.local"
    scheduler_enabled: bool = False
    backend_cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    access_cookie_name: str = "fridgestare_access"
    csrf_cookie_name: str = "fridgestare_csrf"
    csrf_header_name: str = "X-CSRF-Token"
    cookie_secure: bool = False
    # Interactive API docs. Left unset they follow the environment: on locally, off in
    # production, where they only advertise the surface of a single-user app.
    docs_enabled: bool | None = None

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            stripped_value = value.strip()
            if not stripped_value:
                return []
            if stripped_value.startswith("["):
                decoded_value = json.loads(stripped_value)
                if not isinstance(decoded_value, list):
                    raise ValueError("backend_cors_origins JSON value must be a list")
                return [str(item).strip() for item in decoded_value if str(item).strip()]
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("cookie_secure", mode="before")
    @classmethod
    def set_cookie_secure(cls, value: bool | str) -> bool:
        if isinstance(value, bool):
            return value
        return value.lower() in {"1", "true", "yes", "on"}

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() == "production"

    @property
    def mailgun_configured(self) -> bool:
        return bool(self.mailgun_api_key.strip() and self.mailgun_domain.strip())

    @property
    def docs_url(self) -> str | None:
        enabled = not self.is_production if self.docs_enabled is None else self.docs_enabled
        return "/docs" if enabled else None

    @property
    def openapi_url(self) -> str | None:
        return "/openapi.json" if self.docs_url else None

    @model_validator(mode="after")
    def validate_deployment(self) -> "Settings":
        """Refuse to boot a production instance that is quietly insecure or inert.

        Every one of these is a misconfiguration that looks fine at runtime: the app
        starts, serves pages and logs nothing unusual, while sessions are forgeable,
        cookies travel in the clear, or the weekly email never leaves the machine.
        Failing at startup is the only point where the operator is watching.
        """
        if not self.is_production:
            return self

        problems: list[str] = []

        if self.app_secret_key.strip() == PLACEHOLDER_SECRET_KEY:
            problems.append(
                "APP_SECRET_KEY is still the example placeholder. Generate one with "
                "`openssl rand -base64 48`."
            )
        elif len(self.app_secret_key.strip()) < MINIMUM_SECRET_KEY_LENGTH:
            problems.append(
                f"APP_SECRET_KEY must be at least {MINIMUM_SECRET_KEY_LENGTH} characters."
            )

        base_url = str(self.app_base_url)
        if base_url.startswith("https://") and not self.cookie_secure:
            problems.append(
                "COOKIE_SECURE must be true when APP_BASE_URL is https, otherwise the "
                "session cookie is sent over plain HTTP too."
            )
        if base_url.startswith("http://"):
            problems.append(
                "APP_BASE_URL must be an https URL in production; plan emails link to it "
                "and session cookies are scoped to it."
            )

        if self.scheduler_enabled and not self.mailgun_configured:
            problems.append(
                "SCHEDULER_ENABLED is true but Mailgun is not configured, so the weekly "
                "email would be generated and then thrown away. Set MAILGUN_API_KEY and "
                "MAILGUN_DOMAIN, or disable the scheduler."
            )

        if self.mailgun_configured and self.mail_from_address.strip().endswith(".local"):
            problems.append(
                "MAIL_FROM_ADDRESS is still the .local placeholder; Mailgun will reject it. "
                "Use an address on your Mailgun sending domain."
            )

        if problems:
            raise ValueError("Invalid production configuration:\n  - " + "\n  - ".join(problems))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
