import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env", ROOT_DIR / ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Fridgestare"
    api_prefix: str = "/api"
    database_url: str = "mysql+pymysql://fridgestare:fridgestare@localhost:3306/fridgestare?charset=utf8mb4"
    app_secret_key: str = "change-me-with-at-least-32-characters"
    app_base_url: AnyHttpUrl = "http://localhost:8000"
    access_token_expire_minutes: int = 60 * 24 * 7
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4.1-mini"
    tavily_api_key: str = ""
    mailgun_api_key: str = ""
    mailgun_domain: str = ""
    mail_from_address: str = "hello@fridgestare.local"
    scheduler_enabled: bool = False
    backend_cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    access_cookie_name: str = "fridgestare_access"
    csrf_cookie_name: str = "fridgestare_csrf"
    csrf_header_name: str = "X-CSRF-Token"
    cookie_secure: bool = False

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


@lru_cache
def get_settings() -> Settings:
    return Settings()

