from app.controllers.wishlist.wishlist import (
    create_wishlist_item_controller,
    delete_wishlist_item_controller,
    get_wishlist_controller,
    get_wishlist_item_controller,
    update_wishlist_item_controller,
)


def create_wishlist_item_view(name: str, category: str):
    item = create_wishlist_item_controller(name, category)
    return item


def get_wishlist_item_view(id: int):
    item = get_wishlist_item_controller(id)
    return item


def get_wishlist_view():
    items = get_wishlist_controller()
    return items


def update_wishlist_item_view(id: int, name: str | None = None, category: str | None = None):
    item = update_wishlist_item_controller(id, name, category)
    return item


def delete_wishlist_item_view(id: int) -> bool:
    return delete_wishlist_item_controller(id)
