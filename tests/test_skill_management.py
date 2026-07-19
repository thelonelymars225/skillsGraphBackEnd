from fastapi.testclient import TestClient

from main import app


def _create(client: TestClient, name: str = "Management API design") -> dict:
    response = client.post(
        "/api/v1/skills",
        json={"name": name, "category_id": 1, "status": "wishlist"},
    )
    assert response.status_code == 201
    return response.json()


def test_list_edit_archive_and_restore_skill() -> None:
    with TestClient(app) as client:
        skill = _create(client)

        listed = client.get("/api/v1/skills")
        assert listed.status_code == 200
        assert skill["id"] in [item["id"] for item in listed.json()]

        edited = client.put(
            f"/api/v1/skills/{skill['id']}",
            json={"name": " API   architecture ", "category_id": 2, "status": "learning"},
        )
        assert edited.status_code == 200
        assert edited.json()["name"] == "API architecture"
        assert edited.json()["category_id"] == 2
        assert edited.json()["status"] == "learning"

        archived = client.post(f"/api/v1/skills/{skill['id']}/archive")
        assert archived.status_code == 200
        assert archived.json()["status"] == "archived"
        assert archived.json()["archived_at"] is not None
        assert skill["id"] not in [item["id"] for item in client.get("/api/v1/skills").json()]
        assert skill["id"] in [item["id"] for item in client.get("/api/v1/skills?include_archived=true").json()]

        restored = client.post(f"/api/v1/skills/{skill['id']}/restore")
        assert restored.status_code == 200
        assert restored.json()["status"] == "wishlist"
        assert restored.json()["archived_at"] is None
        assert skill["id"] in [item["id"] for item in client.get("/api/v1/skills").json()]


def test_edit_and_restore_preserve_active_name_uniqueness() -> None:
    with TestClient(app) as client:
        first = _create(client, "Management Angular")
        second = _create(client, "Management FastAPI")
        conflict = client.put(
            f"/api/v1/skills/{second['id']}",
            json={"name": " management angular ", "category_id": 1, "status": "learning"},
        )
        assert conflict.status_code == 409

        assert client.post(f"/api/v1/skills/{first['id']}/archive").status_code == 200
        replacement = _create(client, "MANAGEMENT ANGULAR")
        restore_conflict = client.post(f"/api/v1/skills/{first['id']}/restore")
        assert restore_conflict.status_code == 409
        archived = client.get("/api/v1/skills?include_archived=true").json()
        assert next(item for item in archived if item["id"] == first["id"])["status"] == "archived"
        assert replacement["status"] == "wishlist"


def test_management_returns_not_found_and_category_validation() -> None:
    with TestClient(app) as client:
        skill = _create(client)
        assert client.post("/api/v1/skills/999/archive").status_code == 404
        assert client.post("/api/v1/skills/999/restore").status_code == 404
        invalid_category = client.put(
            f"/api/v1/skills/{skill['id']}",
            json={"name": "API design", "category_id": 999, "status": "learning"},
        )
        assert invalid_category.status_code == 404
