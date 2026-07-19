from contextlib import AbstractContextManager
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.database import get_engine
from app.entities import Base
from main import app


class SuccessfulConnection(AbstractContextManager["SuccessfulConnection"]):
    def execute(self, statement: Any) -> None:
        assert str(statement) == "SELECT 1"

    def __exit__(self, *args: object) -> None:
        return None


class SuccessfulEngine:
    def connect(self) -> SuccessfulConnection:
        return SuccessfulConnection()


class UnavailableEngine:
    def connect(self) -> None:
        raise OperationalError(
            "SELECT 1",
            {},
            RuntimeError("postgresql+psycopg://secret:secret@private.example/db"),
        )


def test_application_and_entities_import() -> None:
    assert app
    assert Base.metadata.tables


def test_root_route_is_preserved() -> None:
    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_application_health() -> None:
    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_database_health_success() -> None:
    app.dependency_overrides[get_engine] = SuccessfulEngine
    try:
        response = TestClient(app).get("/api/v1/health/db")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"database": "ok"}


def test_database_health_failure_is_stable_and_does_not_leak_details() -> None:
    app.dependency_overrides[get_engine] = UnavailableEngine
    try:
        response = TestClient(app).get("/api/v1/health/db")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"database": "unavailable"}
    assert "secret" not in response.text
    assert "private.example" not in response.text


def test_old_database_health_route_is_absent() -> None:
    response = TestClient(app).get("/health/db")

    assert response.status_code == 404


def test_allowed_cors_preflight() -> None:
    response = TestClient(app).options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:4200",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-Test-Header",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:4200"
    assert response.headers["access-control-allow-methods"] == "GET, POST"
    assert response.headers["access-control-allow-headers"] == "X-Test-Header"
    assert "access-control-allow-credentials" not in response.headers


def test_unlisted_cors_origin_is_rejected() -> None:
    response = TestClient(app).options(
        "/api/v1/health",
        headers={
            "Origin": "https://unlisted.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
