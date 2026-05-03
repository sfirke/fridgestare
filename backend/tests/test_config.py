from app.core.config import Settings


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