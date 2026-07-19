"""Unify skill lifecycle and persist categories.

Revision ID: 9f4c2a1b7d8e
Revises: c20282939fe3
Create Date: 2026-07-19

The upgrade consolidates case-insensitive duplicate skills and folds the legacy
wishlist table into ``skills``. Consequently, a downgrade cannot reconstruct
the original duplicate rows or determine which unified rows originally came
from ``wishlist``. The compatibility downgrade therefore emits one legacy skill
row per unified skill and recreates an empty wishlist table.
"""

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import Connection


revision: str = "9f4c2a1b7d8e"
down_revision: Union[str, Sequence[str], None] = "c20282939fe3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SEED_CATEGORIES = {
    "frontend": (1, "Frontend"),
    "backend": (2, "Backend"),
    "devops": (3, "DevOps"),
    "tools": (4, "Tools"),
    "data": (5, "Data"),
}
ALLOWED_STATUSES = {"wishlist", "learning", "practiced", "paused", "archived"}
NORMALIZE_SQL = sa.text(
    "SELECT lower(regexp_replace(regexp_replace(CAST(:value AS text), "
    "'^[[:space:]]+|[[:space:]]+$', '', 'g'), '[[:space:]]+', ' ', 'g'))"
)
DISPLAY_SQL = sa.text(
    "SELECT regexp_replace(regexp_replace(CAST(:value AS text), "
    "'^[[:space:]]+|[[:space:]]+$', '', 'g'), '[[:space:]]+', ' ', 'g')"
)


def _normalize(connection: Connection, value: str) -> str:
    return str(connection.execute(NORMALIZE_SQL, {"value": value}).scalar_one())


def _display(connection: Connection, value: str) -> str:
    return str(connection.execute(DISPLAY_SQL, {"value": value}).scalar_one())


def _status(value: str) -> str:
    normalized = value.strip().lower()
    return normalized if normalized in ALLOWED_STATUSES else "practiced"


def _source_rows(connection: Connection) -> tuple[list[dict[str, Any]], int]:
    skill_rows = [
        {
            **dict(row),
            "source": "skills",
            "source_priority": 0,
            "mapped_status": _status(str(row.status)),
        }
        for row in connection.execute(
            sa.text(
                "SELECT id, name, category, status, hours "
                "FROM skills ORDER BY id"
            )
        ).mappings()
    ]
    wishlist_rows = [
        {
            **dict(row),
            "source": "wishlist",
            "source_priority": 1,
            "mapped_status": "wishlist",
            "hours": 0,
        }
        for row in connection.execute(
            sa.text("SELECT id, name, category FROM wishlist ORDER BY id")
        ).mappings()
    ]
    rows = skill_rows + wishlist_rows

    reserved_names: set[str] = set()
    for row in rows:
        display_name = _display(connection, str(row["name"]))
        normalized_name = _normalize(connection, display_name)
        if normalized_name:
            row["display_name"] = display_name
            row["normalized_name"] = normalized_name
            reserved_names.add(normalized_name)

    blank_rows = sorted(
        (row for row in rows if "normalized_name" not in row),
        key=lambda row: (row["source_priority"], row["id"]),
    )
    for row in blank_rows:
        source = row["source"]
        source_id = row["id"]
        candidate = f"Untitled legacy skill ({source} #{source_id})"
        normalized_candidate = _normalize(connection, candidate)
        ordinal = 1
        while normalized_candidate in reserved_names:
            candidate = (
                f"Untitled legacy skill ({source} #{source_id}) "
                f"[legacy-generated:{source}:{source_id}:{ordinal}]"
            )
            normalized_candidate = _normalize(connection, candidate)
            ordinal += 1
        row["display_name"] = candidate
        row["normalized_name"] = normalized_candidate
        reserved_names.add(normalized_candidate)

    max_skill_id = max((int(row["id"]) for row in skill_rows), default=0)
    return rows, max_skill_id


def _categories(
    connection: Connection, rows: list[dict[str, Any]], captured_at: datetime
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    category_candidates: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
    needs_uncategorized = False

    for row in rows:
        display_name = _display(connection, str(row["category"]))
        normalized_name = _normalize(connection, display_name)
        if not normalized_name:
            needs_uncategorized = True
            row["category_normalized_name"] = "uncategorized"
            continue
        row["category_normalized_name"] = normalized_name
        category_candidates[normalized_name].append(
            (row["source_priority"], int(row["id"]), display_name)
        )

    if needs_uncategorized and "uncategorized" not in category_candidates:
        category_candidates["uncategorized"].append((2, 0, "Uncategorized"))

    category_rows: list[dict[str, Any]] = []
    category_ids: dict[str, int] = {}
    for normalized_name, (category_id, display_name) in SEED_CATEGORIES.items():
        category_ids[normalized_name] = category_id
        category_rows.append(
            {
                "id": category_id,
                "name": display_name,
                "created_at": captured_at,
                "updated_at": captured_at,
            }
        )

    non_seed_names = sorted(set(category_candidates) - set(SEED_CATEGORIES))
    for category_id, normalized_name in enumerate(non_seed_names, start=6):
        display_name = min(category_candidates[normalized_name])[-1]
        category_ids[normalized_name] = category_id
        category_rows.append(
            {
                "id": category_id,
                "name": display_name,
                "created_at": captured_at,
                "updated_at": captured_at,
            }
        )

    return category_rows, category_ids


def _skills(
    rows: list[dict[str, Any]],
    max_skill_id: int,
    category_ids: dict[str, int],
    captured_at: datetime,
) -> tuple[list[dict[str, Any]], dict[int, int]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row["normalized_name"]].append(row)

    wishlist_only_names = sorted(
        normalized_name
        for normalized_name, group in groups.items()
        if not any(row["source"] == "skills" for row in group)
    )
    wishlist_ids = {
        normalized_name: max_skill_id + offset
        for offset, normalized_name in enumerate(wishlist_only_names, start=1)
    }

    skill_rows: list[dict[str, Any]] = []
    canonical_skill_ids: dict[int, int] = {}
    for normalized_name in sorted(groups):
        group = groups[normalized_name]
        existing = sorted(
            (row for row in group if row["source"] == "skills"),
            key=lambda row: row["id"],
        )
        if existing:
            canonical = existing[0]
            canonical_id = int(canonical["id"])
            non_archived = [
                row for row in existing if row["mapped_status"] != "archived"
            ]
            if not non_archived:
                status = "archived"
            elif canonical["mapped_status"] != "archived":
                status = canonical["mapped_status"]
            else:
                status = non_archived[0]["mapped_status"]
            legacy_hours = sum(int(row["hours"]) for row in existing)
            for row in existing:
                canonical_skill_ids[int(row["id"])] = canonical_id
        else:
            canonical = min(group, key=lambda row: row["id"])
            canonical_id = wishlist_ids[normalized_name]
            status = "wishlist"
            legacy_hours = 0

        skill_rows.append(
            {
                "id": canonical_id,
                "name": canonical["display_name"],
                "category_id": category_ids[canonical["category_normalized_name"]],
                "status": status,
                "legacy_hours": legacy_hours,
                "created_at": captured_at,
                "updated_at": captured_at,
                "archived_at": captured_at if status == "archived" else None,
            }
        )

    return skill_rows, canonical_skill_ids


def _create_target_tables() -> tuple[sa.Table, sa.Table, sa.Table]:
    categories = op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "normalized_name",
            sa.String(),
            sa.Computed(
                "lower(regexp_replace(regexp_replace(name, "
                "'^[[:space:]]+|[[:space:]]+$', '', 'g'), "
                "'[[:space:]]+', ' ', 'g'))",
                persisted=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "normalized_name <> ''", name="ck_categories_normalized_name_not_blank"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_categories"),
        sa.UniqueConstraint("normalized_name", name="uq_categories_normalized_name"),
    )
    skills = op.create_table(
        "skills_unified",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "normalized_name",
            sa.String(),
            sa.Computed(
                "lower(regexp_replace(regexp_replace(name, "
                "'^[[:space:]]+|[[:space:]]+$', '', 'g'), "
                "'[[:space:]]+', ' ', 'g'))",
                persisted=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "category_id",
            sa.Integer(),
            sa.ForeignKey(
                "categories.id",
                name="fk_skills_category_id_categories",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column(
            "legacy_hours",
            sa.BigInteger(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "normalized_name <> ''", name="ck_skills_normalized_name_not_blank"
        ),
        sa.CheckConstraint(
            "status IN ('wishlist', 'learning', 'practiced', 'paused', 'archived')",
            name="ck_skills_status",
        ),
        sa.CheckConstraint(
            "(status = 'archived') = (archived_at IS NOT NULL)",
            name="ck_skills_archive_state",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_skills"),
    )
    skills_projects = op.create_table(
        "skills_projects_unified",
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["skill_id"],
            ["skills_unified.id"],
            name="fk_skills_projects_skill_id_skills",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_skills_projects_project_id_projects",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "skill_id", "project_id", name="pk_skills_projects"
        ),
    )
    return categories, skills, skills_projects


def upgrade() -> None:
    connection = op.get_bind()
    captured_at = datetime.now(timezone.utc)
    source_rows, max_skill_id = _source_rows(connection)
    category_rows, category_ids = _categories(connection, source_rows, captured_at)
    skill_rows, canonical_skill_ids = _skills(
        source_rows, max_skill_id, category_ids, captured_at
    )
    legacy_links = connection.execute(
        sa.text("SELECT skill_id, project_id FROM skills_projects")
    ).mappings()
    canonical_links = sorted(
        {
            (canonical_skill_ids[int(row["skill_id"])], int(row["project_id"]))
            for row in legacy_links
        }
    )

    categories, skills, skills_projects = _create_target_tables()
    connection.execute(categories.insert(), category_rows)
    if skill_rows:
        connection.execute(skills.insert(), skill_rows)
    if canonical_links:
        connection.execute(
            skills_projects.insert(),
            [
                {"skill_id": skill_id, "project_id": project_id}
                for skill_id, project_id in canonical_links
            ],
        )

    assert connection.execute(
        sa.text("SELECT count(*) FROM skills_unified")
    ).scalar_one() == len(skill_rows)
    assert connection.execute(
        sa.text("SELECT count(*) FROM skills_projects_unified")
    ).scalar_one() == len(canonical_links)

    op.drop_table("skills_projects")
    op.drop_table("wishlist")
    op.drop_table("skills")
    op.rename_table("skills_unified", "skills")
    op.rename_table("skills_projects_unified", "skills_projects")
    op.create_index(
        "uq_skills_active_normalized_name",
        "skills",
        ["normalized_name"],
        unique=True,
        postgresql_where=sa.text("status <> 'archived'"),
    )
    next_category_id = max(row["id"] for row in category_rows) + 1
    next_skill_id = max((row["id"] for row in skill_rows), default=0) + 1
    op.execute(
        sa.text(
            f"ALTER TABLE categories ALTER COLUMN id RESTART WITH {next_category_id}"
        )
    )
    op.execute(
        sa.text(f"ALTER TABLE skills ALTER COLUMN id RESTART WITH {next_skill_id}")
    )


def downgrade() -> None:
    connection = op.get_bind()
    skills_legacy = op.create_table(
        "skills_legacy",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("hours", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_skills_legacy"),
    )
    wishlist_legacy = op.create_table(
        "wishlist_legacy",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_wishlist_legacy"),
    )
    skills_projects_legacy = op.create_table(
        "skills_projects_legacy",
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["skill_id"], ["skills_legacy.id"], name="fk_legacy_links_skill"
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name="fk_legacy_links_project"
        ),
        sa.PrimaryKeyConstraint(
            "skill_id", "project_id", name="pk_skills_projects_legacy"
        ),
    )
    connection.execute(
        sa.text(
            "INSERT INTO skills_legacy (id, name, category, status, hours) "
            "SELECT s.id, s.name, c.name, s.status, s.legacy_hours "
            "FROM skills AS s JOIN categories AS c ON c.id = s.category_id"
        )
    )
    connection.execute(
        sa.text(
            "INSERT INTO skills_projects_legacy (skill_id, project_id) "
            "SELECT skill_id, project_id FROM skills_projects"
        )
    )

    target_skill_count = connection.execute(
        sa.text("SELECT count(*) FROM skills")
    ).scalar_one()
    target_link_count = connection.execute(
        sa.text("SELECT count(*) FROM skills_projects")
    ).scalar_one()
    assert connection.execute(
        sa.text("SELECT count(*) FROM skills_legacy")
    ).scalar_one() == target_skill_count
    assert connection.execute(
        sa.text("SELECT count(*) FROM skills_projects_legacy")
    ).scalar_one() == target_link_count

    op.drop_index("uq_skills_active_normalized_name", table_name="skills")
    op.drop_table("skills_projects")
    op.drop_table("skills")
    op.drop_table("categories")
    op.rename_table("skills_legacy", "skills")
    op.rename_table("wishlist_legacy", "wishlist")
    op.rename_table("skills_projects_legacy", "skills_projects")

    next_skill_id = connection.execute(
        sa.text("SELECT COALESCE(max(id), 0) + 1 FROM skills")
    ).scalar_one()
    op.execute(
        sa.text(f"ALTER TABLE skills ALTER COLUMN id RESTART WITH {next_skill_id}")
    )
    op.execute(sa.text("ALTER TABLE wishlist ALTER COLUMN id RESTART WITH 1"))
