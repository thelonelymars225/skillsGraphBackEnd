from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Computed,
    DateTime,
    Identity,
    Integer,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.entities.base import Base


NORMALIZED_NAME_EXPRESSION = (
    "lower(regexp_replace(regexp_replace(name, "
    "'^[[:space:]]+|[[:space:]]+$', '', 'g'), '[[:space:]]+', ' ', 'g'))"
)


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint(
            "normalized_name <> ''",
            name="ck_categories_normalized_name_not_blank",
        ),
        PrimaryKeyConstraint("id", name="pk_categories"),
        UniqueConstraint("normalized_name", name="uq_categories_normalized_name"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    normalized_name: Mapped[str] = mapped_column(
        String,
        Computed(NORMALIZED_NAME_EXPRESSION, persisted=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
