from functools import lru_cache

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Fridgestare"
    api_prefix: str = "/api"
    database_url: str = "postgresql+psycopg://fridgestare:fridgestare@localhost:5432/fridgestare"
    test_database_url: str = "postgresql+psycopg://fridgestare:fridgestare@localhost:5432/fridgestare_test"
    app_secret_key: str = "change-me"
    app_base_url: AnyHttpUrl = "http://localhost:8000"
    access_token_expire_minutes: int = 60 * 24 * 7
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4.1-mini"
    tavily_api_key: str = ""
    mailgun_api_key: str = ""
    mailgun_domain: str = ""
    mail_from_address: str = "hello@fridgestare.local"
    scheduler_enabled: bool = False
    backend_cors_origins: list[str] = ["http://localhost:5173"]

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
