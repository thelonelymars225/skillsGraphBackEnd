from sqlalchemy import select
from app.entities.skills import Skills
from app.database import SessionLocal


def create_skill(name: str, category: str, status: str, hours: int) -> Skills:
    db = SessionLocal()
    try:
        skill = Skills(name=name, category=category, status=status, hours=hours)
        db.add(skill)
        db.commit()
        db.refresh(skill)
        return skill
    finally:
        db.close()


def get_skill(id: int) -> Skills | None:
    db = SessionLocal()
    try:
        skill = db.scalar(select(Skills).where(Skills.id == id))
        return skill
    finally:
        db.close()


def get_skills() -> list[Skills]:
    db = SessionLocal()
    try:
        skills = db.scalars(select(Skills)).all()
        return list(skills)
    finally:
        db.close()


def update_skill(
    id: int,
    name: str | None = None,
    category: str | None = None,
    status: str | None = None,
    hours: int | None = None,
) -> Skills | None:
    db = SessionLocal()
    try:
        skill = db.scalar(select(Skills).where(Skills.id == id))
        if skill is None:
            return None
        if name is not None:
            skill.name = name
        if category is not None:
            skill.category = category
        if status is not None:
            skill.status = status
        if hours is not None:
            skill.hours = hours
        db.commit()
        db.refresh(skill)
        return skill
    finally:
        db.close()


def delete_skill(id: int) -> bool:
    db = SessionLocal()
    try:
        skill = db.scalar(select(Skills).where(Skills.id == id))
        if skill is None:
            return False
        db.delete(skill)
        db.commit()
        return True
    finally:
        db.close()