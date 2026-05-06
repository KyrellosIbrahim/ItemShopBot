"""
JSON-based wishlist persistence.

Stores wishlists as a JSON file mapping Discord user IDs (as strings)
to lists of cosmetic item names. Handles corrupt or missing files
gracefully by returning empty data rather than crashing.

File format:
    {
      "123456789": ["Renegade Raider", "Black Knight"],
      "987654321": ["Aerial Assault Trooper"]
    }
"""

import json
import logging
import os

log = logging.getLogger(__name__)


class WishlistStorage:
    """Reads and writes per-user wishlists to a JSON file on disk."""
    def __init__(self, path: str):
        self.path = path

    def load(self) -> dict:
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path) as f:
                data = json.load(f)
            if not isinstance(data, dict):
                log.warning("Wishlist file was not a dict, resetting")
                return {}
            return data
        except (json.JSONDecodeError, IOError) as e:
            log.error("Failed to load wishlist: %s", e)
            return {}

    def save(self, wishlist: dict):
        try:
            with open(self.path, "w") as f:
                json.dump(wishlist, f, indent=2)
        except IOError as e:
            log.error("Failed to save wishlist: %s", e)

    def get_user_items(self, user_id: str) -> list:
        return self.load().get(user_id, [])

    def add_item(self, user_id: str, item: str) -> bool:
        """Returns False if the item was already on the list."""
        wishlist = self.load()
        user_items = wishlist.setdefault(user_id, [])
        if item.lower() in [i.lower() for i in user_items]:
            return False
        user_items.append(item)
        self.save(wishlist)
        return True

    def remove_item(self, user_id: str, item: str) -> str | None:
        """Returns the matched item name, or None if not found."""
        wishlist = self.load()
        user_items = wishlist.get(user_id, [])
        match = next((i for i in user_items if i.lower() == item.lower()), None)
        if match:
            user_items.remove(match)
            self.save(wishlist)
        return match

    def clear_user(self, user_id: str) -> int:
        """Clears a user's wishlist. Returns how many items were removed."""
        wishlist = self.load()
        count = len(wishlist.pop(user_id, []))
        if count:
            self.save(wishlist)
        return count
