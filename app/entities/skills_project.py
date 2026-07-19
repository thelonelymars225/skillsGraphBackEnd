from sqlalchemy import ForeignKey
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.entities.base import Base


class SkillsProjects(Base):
    __tablename__ = "skills_projects"
    __table_args__ = (
        PrimaryKeyConstraint("skill_id", "project_id", name="pk_skills_projects"),
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey(
            "skills.id",
            name="fk_skills_projects_skill_id_skills",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey(
            "projects.id",
            name="fk_skills_projects_project_id_projects",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
