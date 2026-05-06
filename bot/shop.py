"""
Fortnite item shop API client and wishlist matching logic.

Fetches the current daily shop from fortnite-api.com and provides
a matching function to compare shop items against user wishlists.
"""

import logging

import aiohttp

log = logging.getLogger(__name__)

SHOP_URL = "https://fortnite-api.com/v2/shop"
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)


async def fetch_shop_items(session: aiohttp.ClientSession) -> list:
    """
    Fetch the current Fortnite item shop.

    Returns a list of dicts, each with keys:
        name, rarity, type, icon (URL), price (int, V-Bucks).

    Raises Exception if the API returns a non-200 status.
    """
    async with session.get(SHOP_URL, timeout=REQUEST_TIMEOUT) as response:
        if response.status != 200:
            raise Exception(f"Shop API returned {response.status}")
        data = await response.json()

    entries = data.get("data", {}).get("entries", [])
    items = []
    for entry in entries:
        for item in entry.get("brItems", []):
            rarity = item.get("rarity") or {}
            item_type = item.get("type") or {}
            images = item.get("images") or {}
            items.append({
                "name": item.get("name", "Unknown"),
                "rarity": rarity.get("displayValue", "Unknown"),
                "type": item_type.get("displayValue", "Unknown"),
                "icon": images.get("icon") or images.get("smallIcon"),
                "price": entry.get("finalPrice", 0),
            })
    return items


def check_wishlist_matches(items: list, wishlist: dict) -> dict:
    """
    Cross-reference shop items with all user wishlists.

    Args:
        items: List of shop item dicts from fetch_shop_items().
        wishlist: Dict of {user_id: [item_name, ...]} from storage.

    Returns:
        Dict of {user_id: [matched item dicts]} for users with hits.
    """
    item_lookup = {}
    for item in items:
        item_lookup.setdefault(item["name"].lower(), []).append(item)

    matches = {}
    for user_id, wished_items in wishlist.items():
        for wished in wished_items:
            for item in item_lookup.get(wished.lower(), []):
                matches.setdefault(user_id, []).append(item)
    return matches
