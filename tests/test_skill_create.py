from collections.abc import Iterator
from contextlib import contextmanager

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.entities import Category, Skill
from main import app


def _regexp_replace(value: str, pattern: str, replacement: str, flags: str) -> str:
    del replacement, flags
    if pattern.startswith("^"):
        return value.strip()
    return " ".join(value.split())


@contextmanager
def skill_client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def register_regexp_replace(dbapi_connection, connection_record) -> None:
        del connection_record
        dbapi_connection.create_function(
            "regexp_replace", 4, _regexp_replace, deterministic=True
        )

    Category.__table__.create(engine)
    Skill.__table__.create(engine)
    session = Session(engine)
    try:
        session.add_all([Category(id=1, name="Backend"), Category(id=2, name="Frontend")])
        session.commit()
        app.dependency_overrides[get_db] = lambda: session
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        session.close()
        engine.dispose()


def test_create_skill_normalizes_name_and_defaults_to_wishlist() -> None:
    with skill_client() as client:
        response = client.post(
            "/api/v1/skills",
            json={"name": "  API\t  design  ", "category_id": 1},
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] == 1
    assert payload["name"] == "API design"
    assert payload["category_id"] == 1
    assert payload["status"] == "wishlist"
    assert payload["created_at"]
    assert payload["updated_at"]


def test_create_skill_rejects_missing_category_and_active_duplicate() -> None:
    with skill_client() as client:
        missing = client.post(
            "/api/v1/skills",
            json={"name": "FastAPI", "category_id": 99},
        )
        created = client.post(
            "/api/v1/skills",
            json={"name": "Fast API", "category_id": 1, "status": "learning"},
        )
        duplicate = client.post(
            "/api/v1/skills",
            json={"name": "  fast   api ", "category_id": 2},
        )

    assert missing.status_code == 404
    assert missing.json() == {"detail": "Category not found."}
    assert created.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json() == {
        "detail": "An active skill with this name already exists."
    }


def test_create_skill_validation_is_stable_and_does_not_write() -> None:
    invalid_requests = [
        {"name": " \t ", "category_id": 1},
        {"name": "Valid", "category_id": 0},
        {"name": "Valid", "category_id": 1, "status": "archived"},
        {"name": "Valid", "category_id": 1, "status": "invented"},
    ]
    with skill_client() as client:
        responses = [
            client.post("/api/v1/skills", json=request) for request in invalid_requests
        ]
        summary = client.get("/api/v1/dashboard/summary")

    assert [response.status_code for response in responses] == [422, 422, 422, 422]
    assert all("sql" not in response.text.lower() for response in responses)
    assert summary.status_code == 200
    assert summary.json()["total_active_skills"] == 0
