from app.services.wishlist.wishlist import (
    create_wishlist_item,
    delete_wishlist_item,
    get_wishlist,
    get_wishlist_item,
    update_wishlist_item,
)


def create_wishlist_item_controller(name: str, category: str):
    item = create_wishlist_item(name, category)
    return item


def get_wishlist_item_controller(id: int):
    item = get_wishlist_item(id)
    return item


def get_wishlist_controller():
    items = get_wishlist()
    return items


def update_wishlist_item_controller(id: int, name: str | None = None, category: str | None = None):
    item = update_wishlist_item(id, name, category)
    return item


def delete_wishlist_item_controller(id: int) -> bool:
    return delete_wishlist_item(id)
