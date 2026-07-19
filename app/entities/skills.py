from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Computed,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.entities.base import Base
from app.entities.category import NORMALIZED_NAME_EXPRESSION


class Skill(Base):
    __tablename__ = "skills"
    __table_args__ = (
        CheckConstraint(
            "normalized_name <> ''", name="ck_skills_normalized_name_not_blank"
        ),
        CheckConstraint(
            "status IN ('wishlist', 'learning', 'practiced', 'paused', 'archived')",
            name="ck_skills_status",
        ),
        CheckConstraint(
            "(status = 'archived') = (archived_at IS NOT NULL)",
            name="ck_skills_archive_state",
        ),
        PrimaryKeyConstraint("id", name="pk_skills"),
        Index(
            "uq_skills_active_normalized_name",
            "normalized_name",
            unique=True,
            postgresql_where=text("status <> 'archived'"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    normalized_name: Mapped[str] = mapped_column(
        String,
        Computed(NORMALIZED_NAME_EXPRESSION, persisted=True),
        nullable=False,
    )
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "categories.id",
            name="fk_skills_category_id_categories",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    legacy_hours: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
