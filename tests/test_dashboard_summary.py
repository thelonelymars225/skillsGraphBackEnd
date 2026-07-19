from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import get_db
from main import app


def dashboard_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE categories (id INTEGER PRIMARY KEY, name VARCHAR NOT NULL)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE skills ("
                "id INTEGER PRIMARY KEY, name VARCHAR NOT NULL, category_id INTEGER NOT NULL, "
                "status VARCHAR NOT NULL, archived_at DATETIME NULL)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO categories (id, name) VALUES "
                "(1, 'Backend'), (2, 'Frontend'), (3, 'Data')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO skills (id, name, category_id, status, archived_at) VALUES "
                "(1, 'FastAPI', 1, 'learning', NULL), "
                "(2, 'PostgreSQL', 1, 'practiced', NULL), "
                "(3, 'Angular', 2, 'wishlist', NULL), "
                "(4, 'Old tool', 1, 'archived', '2026-07-01 00:00:00')"
            )
        )

    with Session(engine) as session:
        yield session


def test_summary_returns_unfiltered_inventory_and_zero_complete_breakdowns() -> None:
    app.dependency_overrides[get_db] = dashboard_session
    try:
        response = TestClient(app).get("/api/v1/dashboard/summary")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "total_active_skills": 3,
        "archived_skill_count": 1,
        "visible_skill_count": 3,
        "counts_by_status": {
            "wishlist": 1,
            "learning": 1,
            "practiced": 1,
            "paused": 0,
        },
        "counts_by_category": [
            {"category_id": 1, "category_name": "Backend", "skill_count": 2},
            {"category_id": 3, "category_name": "Data", "skill_count": 0},
            {"category_id": 2, "category_name": "Frontend", "skill_count": 1},
        ],
    }


def test_filters_only_change_visible_skill_count() -> None:
    app.dependency_overrides[get_db] = dashboard_session
    try:
        response = TestClient(app).get(
            "/api/v1/dashboard/summary",
            params={"status": "learning", "category_id": 1},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["visible_skill_count"] == 1
    assert payload["total_active_skills"] == 3
    assert payload["archived_skill_count"] == 1
    assert payload["counts_by_status"]["wishlist"] == 1
    assert payload["counts_by_category"][0]["skill_count"] == 2


def test_filters_reject_archived_status_and_non_positive_category_ids() -> None:
    client = TestClient(app)

    assert client.get(
        "/api/v1/dashboard/summary", params={"status": "archived"}
    ).status_code == 422
    assert client.get(
        "/api/v1/dashboard/summary", params={"category_id": 0}
    ).status_code == 422
