from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.entities import Category, Skill
from app.schemas.skills import SkillCreate, SkillUpdate


class SkillCategoryNotFoundError(Exception):
    pass


class ActiveSkillNameConflictError(Exception):
    pass


class SkillNotFoundError(Exception):
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


def list_skills(db: Session, *, include_archived: bool = False) -> list[Skill]:
    query = select(Skill).order_by(Skill.name, Skill.id)
    if not include_archived:
        query = query.where(Skill.status != "archived")
    return list(db.scalars(query))


def _get_skill(db: Session, skill_id: int) -> Skill:
    skill = db.get(Skill, skill_id)
    if skill is None:
        raise SkillNotFoundError
    return skill


def _ensure_active_name_available(db: Session, name: str, skill_id: int) -> None:
    duplicate_id = db.scalar(
        select(Skill.id).where(
            Skill.normalized_name == name.lower(),
            Skill.status != "archived",
            Skill.id != skill_id,
        )
    )
    if duplicate_id is not None:
        raise ActiveSkillNameConflictError


def update_skill(db: Session, skill_id: int, update: SkillUpdate) -> Skill:
    skill = _get_skill(db, skill_id)
    if skill.status == "archived":
        raise SkillNotFoundError
    if db.get(Category, update.category_id) is None:
        raise SkillCategoryNotFoundError
    _ensure_active_name_available(db, update.name, skill_id)
    skill.name = update.name
    skill.category_id = update.category_id
    skill.status = update.status
    skill.updated_at = datetime.now(timezone.utc)
    return _commit_skill(db, skill)


def archive_skill(db: Session, skill_id: int) -> Skill:
    skill = _get_skill(db, skill_id)
    if skill.status != "archived":
        now = datetime.now(timezone.utc)
        skill.status = "archived"
        skill.archived_at = now
        skill.updated_at = now
        return _commit_skill(db, skill)
    return skill


def restore_skill(db: Session, skill_id: int) -> Skill:
    skill = _get_skill(db, skill_id)
    if skill.status == "archived":
        _ensure_active_name_available(db, skill.name, skill_id)
        skill.status = "wishlist"
        skill.archived_at = None
        skill.updated_at = datetime.now(timezone.utc)
        return _commit_skill(db, skill)
    return skill


def _commit_skill(db: Session, skill: Skill) -> Skill:
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ActiveSkillNameConflictError from error
    db.refresh(skill)
    return skill
