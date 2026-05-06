"""
Core bot class for the Fortnite Item Shop Bot.

Defines ItemShopBot, which handles:
- Connecting to Discord and managing the bot lifecycle.
- Running a daily scheduled task to fetch the Fortnite item shop.
- Cross-referencing the shop with user wishlists.
- Sending per-user embed "card" alerts when wishlist items appear.
"""

import datetime
import logging

import aiohttp
import discord
from discord.ext import commands, tasks

from bot.shop import fetch_shop_items, check_wishlist_matches
from bot.storage import WishlistStorage

log = logging.getLogger(__name__)

RARITY_COLORS = {
    "Legendary": 0xF0A01E,
    "Epic": 0xB946ED,
    "Rare": 0x3F9EE0,
    "Uncommon": 0x6ABB2B,
    "Common": 0x8C8C8C,
}


class ItemShopBot(commands.Bot):
    """
    Discord bot that monitors the Fortnite item shop daily and alerts
    users when their wishlisted cosmetics become available.

    Args:
        channel_id: The Discord channel ID to post shop alerts in.
        wishlist_path: File path to the JSON wishlist storage.
    """

    def __init__(self, channel_id: int, wishlist_path: str, fortnite_api_key: str):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

        self.channel_id = channel_id
        self.fortnite_api_key = fortnite_api_key
        self.storage = WishlistStorage(wishlist_path)
        self.session: aiohttp.ClientSession | None = None

    async def setup_hook(self):
        self.session = aiohttp.ClientSession(headers={"Authorization": self.fortnite_api_key})
        await self.load_extension("bot.cogs.wishlist")
        await self.tree.sync()
        self.daily_shop_check.start()
        log.info("Bot setup complete, task loop started")

    async def close(self):
        self.daily_shop_check.cancel()
        if self.session:
            await self.session.close()
        await super().close()

    async def on_ready(self):
        log.info("Logged in as %s", self.user)

    @tasks.loop(time=datetime.time(hour=0, minute=2, tzinfo=datetime.timezone.utc))
    async def daily_shop_check(self):
        channel = self.get_channel(self.channel_id) or await self.fetch_channel(self.channel_id)
        if not channel:
            log.error("Could not find channel %s", self.channel_id)
            return

        try:
            items = await fetch_shop_items(self.session)
        except Exception:
            log.exception("Failed to fetch item shop")
            await channel.send("Failed to fetch the item shop. Will try again tomorrow.")
            return

        wishlist = self.storage.load()
        matches = check_wishlist_matches(items, wishlist)

        if not matches:
            await channel.send("No wishlist items in the shop today. 😿")
            return

        for user_id, matched_items in matches.items():
            try:
                user = await self.fetch_user(int(user_id))
            except discord.NotFound:
                continue

            embed = discord.Embed(
                title=f"🚨 WISHLIST ALERT {user.display_name}! 🚨",
                description=f"{user.mention}, YOU HAVE ITEM(S) IN THE SHOP!",
                color=0xFF4500,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )

            for item in matched_items:
                price_str = f"{item['price']:,} V-Bucks"
                rarity = item["rarity"]
                item_type = item["type"]
                embed.add_field(
                    name=item["name"],
                    value=f"{rarity} {item_type}\n{price_str}",
                    inline=True,
                )

            if matched_items[0].get("icon"):
                embed.set_thumbnail(url=matched_items[0]["icon"])

            embed.set_footer(text="Fortnite Item Shop")
            await channel.send(embed=embed)

    @daily_shop_check.before_loop
    async def before_daily_shop_check(self):
        await self.wait_until_ready()

    @daily_shop_check.error
    async def daily_shop_check_error(self, error):
        log.exception("Daily shop check crashed, it will retry next cycle", exc_info=error)
