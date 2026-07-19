from sqlalchemy import select
from app.entities.wishlist import Wishlist
from app.database import SessionLocal


def create_wishlist_item(name: str, category: str) -> Wishlist:
    db = SessionLocal()
    try:
        item = Wishlist(name=name, category=category)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    finally:
        db.close()


def get_wishlist_item(id: int) -> Wishlist | None:
    db = SessionLocal()
    try:
        item = db.scalar(select(Wishlist).where(Wishlist.id == id))
        return item
    finally:
        db.close()


def get_wishlist() -> list[Wishlist]:
    db = SessionLocal()
    try:
        items = db.scalars(select(Wishlist)).all()
        return list(items)
    finally:
        db.close()


def update_wishlist_item(id: int, name: str | None = None, category: str | None = None) -> Wishlist | None:
    db = SessionLocal()
    try:
        item = db.scalar(select(Wishlist).where(Wishlist.id == id))
        if item is None:
            return None
        if name is not None:
            item.name = name
        if category is not None:
            item.category = category
        db.commit()
        db.refresh(item)
        return item
    finally:
        db.close()


def delete_wishlist_item(id: int) -> bool:
    db = SessionLocal()
    try:
        item = db.scalar(select(Wishlist).where(Wishlist.id == id))
        if item is None:
            return False
        db.delete(item)
        db.commit()
        return True
    finally:
        db.close()
