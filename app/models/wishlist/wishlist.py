from pydantic import BaseModel, ConfigDict


class WishlistCreate(BaseModel):
    name: str
    category: str


class WishlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
