from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.entities.base import Base



# an example mapping using the base
class Skills(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    category: Mapped[str]
    status: Mapped[str]
    hours: Mapped[int]
d