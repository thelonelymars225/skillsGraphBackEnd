import pytest
from pydantic import ValidationError

from app.config import Settings


def test_database_url_is_required_without_env_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_valid_environment_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    database_url = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/skills_graph"
    )
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("CORS_ORIGINS", '["http://localhost:4200"]')

    loaded = Settings(_env_file=None)

    assert loaded.database_url == database_url
    assert loaded.cors_origins == ["http://localhost:4200"]


def test_cors_origins_default_to_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/skills_graph",
    )
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    loaded = Settings(_env_file=None)

    assert loaded.cors_origins == []
