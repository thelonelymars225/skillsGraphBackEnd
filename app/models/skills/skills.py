from pydantic import BaseModel, ConfigDict


class SkillCreate(BaseModel):
    name: str
    category: str
    status: str
    hours: int


class SkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    status: str
    hours: int
