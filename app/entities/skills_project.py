from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship


from app.entities.base import Base


class SkillsProjects(Base):
    __tablename__ = "skills_projects"
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), primary_key=True)


