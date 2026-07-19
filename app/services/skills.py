from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.entities import Category, Skill
from app.schemas.skills import SkillCreate


class SkillCategoryNotFoundError(Exception):
    pass


class ActiveSkillNameConflictError(Exception):
    pass


def create_skill(db: Session, skill_create: SkillCreate) -> Skill:
    if db.get(Category, skill_create.category_id) is None:
        raise SkillCategoryNotFoundError

    normalized_name = skill_create.name.lower()
    duplicate_id = db.scalar(
        select(Skill.id).where(
            Skill.normalized_name == normalized_name,
            Skill.status != "archived",
        )
    )
    if duplicate_id is not None:
        raise ActiveSkillNameConflictError

    skill = Skill(
        name=skill_create.name,
        category_id=skill_create.category_id,
        status=skill_create.status,
    )
    db.add(skill)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ActiveSkillNameConflictError from error
    db.refresh(skill)
    return skill
