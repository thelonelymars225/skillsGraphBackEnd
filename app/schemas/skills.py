from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.dashboard import ActiveSkillStatus


CreatableSkillStatus = Literal["wishlist", "learning", "practiced", "paused"]
SkillLifecycleStatus = Literal["wishlist", "learning", "practiced", "paused", "archived"]


def collapse_skill_name(value: str) -> str:
    return " ".join(value.split())


class SkillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category_id: int = Field(gt=0)
    status: CreatableSkillStatus = "wishlist"

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        return collapse_skill_name(value)


class SkillUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category_id: int = Field(gt=0)
    status: CreatableSkillStatus

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        return collapse_skill_name(value)


class SkillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category_id: int
    status: SkillLifecycleStatus
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
