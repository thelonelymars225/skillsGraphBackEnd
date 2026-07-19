from typing import Literal

from pydantic import BaseModel


ActiveSkillStatus = Literal["wishlist", "learning", "practiced", "paused"]


class CategorySkillCount(BaseModel):
    category_id: int
    category_name: str
    skill_count: int


class DashboardSummary(BaseModel):
    total_active_skills: int
    archived_skill_count: int
    visible_skill_count: int
    counts_by_status: dict[ActiveSkillStatus, int]
    counts_by_category: list[CategorySkillCount]
