from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.entities import Category, Skill
from app.schemas.dashboard import (
    ActiveSkillStatus,
    CategorySkillCount,
    DashboardSummary,
)


ACTIVE_SKILL_STATUSES: tuple[ActiveSkillStatus, ...] = (
    "wishlist",
    "learning",
    "practiced",
    "paused",
)


def _active_skills_count() -> Select[tuple[int]]:
    return select(func.count(Skill.id)).where(Skill.status != "archived")


def get_dashboard_summary(
    db: Session,
    *,
    status: ActiveSkillStatus | None = None,
    category_id: int | None = None,
) -> DashboardSummary:
    total_active_skills = db.scalar(_active_skills_count()) or 0
    archived_skill_count = (
        db.scalar(select(func.count(Skill.id)).where(Skill.status == "archived")) or 0
    )

    status_rows = db.execute(
        select(Skill.status, func.count(Skill.id))
        .where(Skill.status != "archived")
        .group_by(Skill.status)
    ).all()
    counts_by_status: dict[ActiveSkillStatus, int] = {
        active_status: 0 for active_status in ACTIVE_SKILL_STATUSES
    }
    for row_status, skill_count in status_rows:
        if row_status in counts_by_status:
            counts_by_status[row_status] = skill_count

    category_rows = db.execute(
        select(Category.id, Category.name, func.count(Skill.id))
        .outerjoin(
            Skill,
            (Skill.category_id == Category.id) & (Skill.status != "archived"),
        )
        .group_by(Category.id, Category.name)
        .order_by(Category.name, Category.id)
    ).all()

    visible_query = _active_skills_count()
    if status is not None:
        visible_query = visible_query.where(Skill.status == status)
    if category_id is not None:
        visible_query = visible_query.where(Skill.category_id == category_id)

    return DashboardSummary(
        total_active_skills=total_active_skills,
        archived_skill_count=archived_skill_count,
        visible_skill_count=db.scalar(visible_query) or 0,
        counts_by_status=counts_by_status,
        counts_by_category=[
            CategorySkillCount(
                category_id=row_category_id,
                category_name=category_name,
                skill_count=skill_count,
            )
            for row_category_id, category_name, skill_count in category_rows
        ],
    )
