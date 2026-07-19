import os
from collections.abc import Iterator
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, inspect
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.entities import Base, Category, Projects, Skill, SkillsProjects


ROOT = Path(__file__).resolve().parents[1]
INITIAL_REVISION = "c20282939fe3"


@pytest.fixture(scope="module")
def migration_engine() -> Iterator[Engine]:
    migration_url = os.environ.get("MIGRATION_TEST_DATABASE_URL")
    if not migration_url:
        pytest.fail(
            "MIGRATION_TEST_DATABASE_URL must identify a disposable PostgreSQL database"
        )
    if migration_url == settings.database_url:
        pytest.fail("migration database must be isolated from DATABASE_URL")

    original_url = settings.database_url
    settings.database_url = migration_url
    engine = sa.create_engine(migration_url)
    try:
        yield engine
    finally:
        engine.dispose()
        settings.database_url = original_url


@pytest.fixture(autouse=True)
def reset_schema(migration_engine: Engine) -> Iterator[None]:
    with migration_engine.connect().execution_options(
        isolation_level="AUTOCOMMIT"
    ) as connection:
        connection.execute(sa.text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(sa.text("CREATE SCHEMA public"))
    yield


def _alembic_config() -> Config:
    return Config(str(ROOT / "alembic.ini"))


def _upgrade(revision: str = "head") -> None:
    command.upgrade(_alembic_config(), revision)


def _downgrade(revision: str) -> None:
    command.downgrade(_alembic_config(), revision)


def _insert_legacy_fixture(engine: Engine) -> None:
    projects = [
        {"id": 1, "name": "One", "description": "one"},
        {"id": 2, "name": "Two", "description": "two"},
        {"id": 3, "name": "Three", "description": "three"},
    ]
    skills = [
        {"id": 1, "name": " Angular ", "category": " Frontend ", "status": " learning ", "hours": 3},
        {"id": 2, "name": "angular", "category": "frontend", "status": "archived", "hours": 4},
        {"id": 3, "name": " PYTHON ", "category": " Backend ", "status": "", "hours": 0},
        {"id": 4, "name": "python", "category": "backend", "status": "unknown", "hours": 5},
        {"id": 5, "name": "Terraform", "category": " DEVOPS ", "status": "paused", "hours": 2},
        {"id": 6, "name": "Git", "category": "Tools", "status": "PRACTICED ", "hours": 1},
        {"id": 7, "name": "SQL", "category": "Data", "status": "wishlist", "hours": 0},
        {"id": 8, "name": "Rust", "category": " Systems ", "status": "archived", "hours": 8},
        {"id": 9, "name": "Docker", "category": "", "status": "archived", "hours": 1},
        {"id": 10, "name": " docker ", "category": "   ", "status": "practiced", "hours": 2},
        {"id": 11, "name": "   ", "category": "Backend", "status": "mystery", "hours": 1},
        {"id": 12, "name": "Untitled legacy skill (skills #11)", "category": "Tools", "status": "practiced", "hours": 0},
        {"id": 13, "name": "Untitled legacy skill (skills #11) [legacy-generated:skills:11:1]", "category": "Tools", "status": "practiced", "hours": 0},
    ]
    wishlist = [
        {"id": 1, "name": " ANGULAR", "category": "Data"},
        {"id": 2, "name": "Kotlin", "category": " Mobile "},
        {"id": 3, "name": "\t ", "category": "Uncategorized"},
        {"id": 4, "name": " kotlin ", "category": "mobile"},
        {"id": 5, "name": "Frontend Only", "category": "Frontend"},
    ]
    links = [
        {"skill_id": 1, "project_id": 1},
        {"skill_id": 2, "project_id": 1},
        {"skill_id": 2, "project_id": 2},
        {"skill_id": 3, "project_id": 1},
        {"skill_id": 4, "project_id": 2},
        {"skill_id": 8, "project_id": 3},
        {"skill_id": 9, "project_id": 1},
        {"skill_id": 10, "project_id": 2},
    ]
    with engine.begin() as connection:
        connection.execute(
            sa.text(
                "INSERT INTO projects (id, name, description) "
                "VALUES (:id, :name, :description)"
            ),
            projects,
        )
        connection.execute(
            sa.text(
                "INSERT INTO skills (id, name, category, status, hours) "
                "VALUES (:id, :name, :category, :status, :hours)"
            ),
            skills,
        )
        connection.execute(
            sa.text(
                "INSERT INTO wishlist (id, name, category) "
                "VALUES (:id, :name, :category)"
            ),
            wishlist,
        )
        connection.execute(
            sa.text(
                "INSERT INTO skills_projects (skill_id, project_id) "
                "VALUES (:skill_id, :project_id)"
            ),
            links,
        )


def _populated_upgrade(engine: Engine) -> None:
    _upgrade(INITIAL_REVISION)
    _insert_legacy_fixture(engine)
    _upgrade()


def _fetch_all(engine: Engine, sql: str) -> list[tuple[object, ...]]:
    with engine.connect() as connection:
        return [tuple(row) for row in connection.execute(sa.text(sql)).all()]


def _assert_integrity_rejected(engine: Engine, sql: str, **parameters: object) -> None:
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(sa.text(sql), parameters)


def test_empty_upgrade_creates_exact_target_schema_and_seeds(
    migration_engine: Engine,
) -> None:
    _upgrade()

    inspector = inspect(migration_engine)
    assert set(inspector.get_table_names()) == {
        "alembic_version",
        "categories",
        "projects",
        "skills",
        "skills_projects",
    }
    assert _fetch_all(
        migration_engine, "SELECT id, name, normalized_name FROM categories ORDER BY id"
    ) == [
        (1, "Frontend", "frontend"),
        (2, "Backend", "backend"),
        (3, "DevOps", "devops"),
        (4, "Tools", "tools"),
        (5, "Data", "data"),
    ]
    assert _fetch_all(migration_engine, "SELECT id FROM skills") == []

    skill_columns = {column["name"]: column for column in inspector.get_columns("skills")}
    assert set(skill_columns) == {
        "id",
        "name",
        "normalized_name",
        "category_id",
        "status",
        "legacy_hours",
        "created_at",
        "updated_at",
        "archived_at",
    }
    assert isinstance(skill_columns["legacy_hours"]["type"], sa.BigInteger)
    assert skill_columns["normalized_name"]["computed"]["persisted"] is True
    assert {check["name"] for check in inspector.get_check_constraints("skills")} == {
        "ck_skills_archive_state",
        "ck_skills_normalized_name_not_blank",
        "ck_skills_status",
    }
    active_index = next(
        index
        for index in inspector.get_indexes("skills")
        if index["name"] == "uq_skills_active_normalized_name"
    )
    assert active_index["unique"] is True
    assert active_index["column_names"] == ["normalized_name"]
    assert "status" in str(active_index["dialect_options"]["postgresql_where"])
    category_fk = inspector.get_foreign_keys("skills")[0]
    assert category_fk["referred_table"] == "categories"
    assert category_fk["options"]["ondelete"] == "RESTRICT"
    link_fks = {
        foreign_key["referred_table"]: foreign_key["options"]["ondelete"]
        for foreign_key in inspector.get_foreign_keys("skills_projects")
    }
    assert link_fks == {"projects": "CASCADE", "skills": "CASCADE"}

    with migration_engine.begin() as connection:
        category_id = connection.execute(
            sa.text(
                "INSERT INTO categories (name) "
                "VALUES (' Security \t Operations ') RETURNING id"
            )
        ).scalar_one()
        skill_id = connection.execute(
            sa.text(
                "INSERT INTO skills (name, category_id, status) "
                "VALUES (' Threat \t modeling ', :category_id, 'wishlist') RETURNING id"
            ),
            {"category_id": category_id},
        ).scalar_one()
    assert (category_id, skill_id) == (6, 1)
    assert _fetch_all(
        migration_engine,
        "SELECT normalized_name FROM categories WHERE id = 6",
    ) == [("security operations",)]
    assert _fetch_all(
        migration_engine,
        "SELECT normalized_name FROM skills WHERE id = 1",
    ) == [("threat modeling",)]


def test_populated_upgrade_consolidates_without_data_or_link_loss(
    migration_engine: Engine,
) -> None:
    _populated_upgrade(migration_engine)

    assert _fetch_all(
        migration_engine, "SELECT id, name, normalized_name FROM categories ORDER BY id"
    ) == [
        (1, "Frontend", "frontend"),
        (2, "Backend", "backend"),
        (3, "DevOps", "devops"),
        (4, "Tools", "tools"),
        (5, "Data", "data"),
        (6, "Mobile", "mobile"),
        (7, "Systems", "systems"),
        (8, "Uncategorized", "uncategorized"),
    ]
    skills = _fetch_all(
        migration_engine,
        "SELECT id, name, normalized_name, category_id, status, legacy_hours, "
        "archived_at IS NOT NULL FROM skills ORDER BY id",
    )
    assert len(skills) == 13
    by_id = {row[0]: row[1:] for row in skills}
    assert by_id[1] == ("Angular", "angular", 1, "learning", 7, False)
    assert by_id[3] == ("PYTHON", "python", 2, "practiced", 5, False)
    assert by_id[5][3:5] == ("paused", 2)
    assert by_id[6][3:5] == ("practiced", 1)
    assert by_id[7][3:5] == ("wishlist", 0)
    assert by_id[8] == ("Rust", "rust", 7, "archived", 8, True)
    assert by_id[9] == ("Docker", "docker", 8, "practiced", 3, False)
    assert by_id[11][:2] == (
        "Untitled legacy skill (skills #11) [legacy-generated:skills:11:2]",
        "untitled legacy skill (skills #11) [legacy-generated:skills:11:2]",
    )
    assert by_id[14][:4] == ("Frontend Only", "frontend only", 1, "wishlist")
    assert by_id[15][:4] == ("Kotlin", "kotlin", 6, "wishlist")
    assert by_id[16][:4] == (
        "Untitled legacy skill (wishlist #3)",
        "untitled legacy skill (wishlist #3)",
        8,
        "wishlist",
    )
    assert _fetch_all(
        migration_engine,
        "SELECT skill_id, project_id FROM skills_projects ORDER BY skill_id, project_id",
    ) == [(1, 1), (1, 2), (3, 1), (3, 2), (8, 3), (9, 1), (9, 2)]
    assert "wishlist" not in inspect(migration_engine).get_table_names()

    with migration_engine.begin() as connection:
        category_id = connection.execute(
            sa.text("INSERT INTO categories (name) VALUES ('Security') RETURNING id")
        ).scalar_one()
        skill_id = connection.execute(
            sa.text(
                "INSERT INTO skills (name, category_id, status) "
                "VALUES ('Threat modeling', :category_id, 'learning') RETURNING id"
            ),
            {"category_id": category_id},
        ).scalar_one()
    assert (category_id, skill_id) == (9, 17)


def test_target_database_enforces_names_lifecycle_and_references(
    migration_engine: Engine,
) -> None:
    _populated_upgrade(migration_engine)

    insert_skill = (
        "INSERT INTO skills (name, category_id, status, archived_at) "
        "VALUES (:name, :category_id, :status, :archived_at)"
    )
    _assert_integrity_rejected(
        migration_engine,
        insert_skill,
        name="Unsupported",
        category_id=1,
        status="expert",
        archived_at=None,
    )
    _assert_integrity_rejected(
        migration_engine,
        insert_skill,
        name="Archive mismatch",
        category_id=1,
        status="archived",
        archived_at=None,
    )
    _assert_integrity_rejected(
        migration_engine,
        insert_skill,
        name="Active mismatch",
        category_id=1,
        status="learning",
        archived_at="2026-07-19T00:00:00+00:00",
    )
    _assert_integrity_rejected(
        migration_engine,
        insert_skill,
        name="  \t ",
        category_id=1,
        status="wishlist",
        archived_at=None,
    )
    _assert_integrity_rejected(
        migration_engine,
        insert_skill,
        name="Orphan",
        category_id=999,
        status="wishlist",
        archived_at=None,
    )
    _assert_integrity_rejected(
        migration_engine,
        insert_skill,
        name="  ANGULAR  ",
        category_id=1,
        status="paused",
        archived_at=None,
    )
    _assert_integrity_rejected(
        migration_engine, "DELETE FROM categories WHERE id = 1"
    )
    _assert_integrity_rejected(
        migration_engine, "INSERT INTO categories (name) VALUES (' \t ')"
    )
    _assert_integrity_rejected(
        migration_engine, "INSERT INTO categories (name) VALUES (' FRONTEND ')"
    )

    with migration_engine.begin() as connection:
        connection.execute(
            sa.text(insert_skill),
            [
                {
                    "name": "Angular",
                    "category_id": 1,
                    "status": "archived",
                    "archived_at": "2026-07-19T00:00:00+00:00",
                },
                {
                    "name": " ANGULAR ",
                    "category_id": 1,
                    "status": "archived",
                    "archived_at": "2026-07-19T01:00:00+00:00",
                },
            ],
        )
    assert _fetch_all(
        migration_engine,
        "SELECT status, count(*) FROM skills WHERE normalized_name = 'angular' "
        "GROUP BY status ORDER BY status",
    ) == [("archived", 2), ("learning", 1)]


def test_entity_metadata_matches_migrated_schema() -> None:
    assert {Category, Skill, Projects, SkillsProjects}
    assert set(Base.metadata.tables) == {
        "categories",
        "skills",
        "projects",
        "skills_projects",
    }
    assert Base.registry._class_registry.get("Wishlist") is None
    assert Base.registry._class_registry.get("Skills") is None

    category_table = Base.metadata.tables["categories"]
    skill_table = Base.metadata.tables["skills"]
    assert category_table.c.normalized_name.computed is not None
    assert skill_table.c.normalized_name.computed is not None
    assert isinstance(skill_table.c.legacy_hours.type, sa.BigInteger)
    assert skill_table.c.category_id.foreign_keys.pop().ondelete == "RESTRICT"
    assert next(
        index
        for index in skill_table.indexes
        if index.name == "uq_skills_active_normalized_name"
    ).unique
    link_table = Base.metadata.tables["skills_projects"]
    assert {foreign_key.ondelete for foreign_key in link_table.foreign_keys} == {
        "CASCADE"
    }


def _logical_snapshot(engine: Engine) -> tuple[list[tuple[object, ...]], ...]:
    return (
        _fetch_all(
            engine,
            "SELECT id, name, normalized_name FROM categories ORDER BY id",
        ),
        _fetch_all(
            engine,
            "SELECT s.id, s.name, c.name, s.status, s.legacy_hours "
            "FROM skills AS s JOIN categories AS c ON c.id = s.category_id "
            "ORDER BY s.id",
        ),
        _fetch_all(
            engine,
            "SELECT skill_id, project_id FROM skills_projects "
            "ORDER BY skill_id, project_id",
        ),
    )


def test_downgrade_and_reupgrade_preserve_unified_logical_data(
    migration_engine: Engine,
) -> None:
    _populated_upgrade(migration_engine)
    before = _logical_snapshot(migration_engine)

    _downgrade(INITIAL_REVISION)
    inspector = inspect(migration_engine)
    assert "categories" not in inspector.get_table_names()
    assert "wishlist" in inspector.get_table_names()
    assert _fetch_all(migration_engine, "SELECT id FROM wishlist") == []
    legacy_columns = {
        column["name"]: column for column in inspector.get_columns("skills")
    }
    assert set(legacy_columns) == {"id", "name", "category", "status", "hours"}
    assert isinstance(legacy_columns["hours"]["type"], sa.BigInteger)
    assert _fetch_all(
        migration_engine,
        "SELECT skill_id, project_id FROM skills_projects ORDER BY skill_id, project_id",
    ) == before[2]

    _upgrade()
    assert _logical_snapshot(migration_engine) == before
