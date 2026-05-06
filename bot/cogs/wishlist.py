"""
Wishlist slash commands for the Item Shop Bot.

Provides the following Discord slash commands:
    /wishadd <item>   — Add a cosmetic to your personal wishlist.
    /wishrm <item>    — Remove a cosmetic from your wishlist.
    /wishview         — View all items on your wishlist.
    /wishclear        — Clear your entire wishlist.

All responses are ephemeral (only visible to the user who ran the command).
"""

import discord
from discord import app_commands
from discord.ext import commands

from bot.storage import WishlistStorage


class WishlistCog(commands.Cog):
    """Cog that registers all wishlist-related slash commands."""
    def __init__(self, bot: commands.Bot, storage: WishlistStorage):
        self.bot = bot
        self.storage = storage

    @app_commands.command(name="wishadd", description="Add an item to your wishlist")
    @app_commands.describe(item="The name of the cosmetic to add")
    async def wishadd(self, interaction: discord.Interaction, item: str):
        user_id = str(interaction.user.id)
        if self.storage.add_item(user_id, item):
            await interaction.response.send_message(
                f"Added **{item}** to your wishlist.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"**{item}** is already on your wishlist.", ephemeral=True
            )

    @app_commands.command(name="wishrm", description="Remove an item from your wishlist")
    @app_commands.describe(item="The name of the cosmetic to remove")
    async def wishrm(self, interaction: discord.Interaction, item: str):
        user_id = str(interaction.user.id)
        match = self.storage.remove_item(user_id, item)
        if match:
            await interaction.response.send_message(
                f"Removed **{match}** from your wishlist.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"**{item}** wasn't found on your wishlist.", ephemeral=True
            )

    @app_commands.command(name="wishview", description="View your wishlist")
    async def wishview(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        items = self.storage.get_user_items(user_id)
        if not items:
            await interaction.response.send_message("Your wishlist is empty.", ephemeral=True)
            return
        listing = "\n".join(f"- {item}" for item in items)
        await interaction.response.send_message(f"**Your wishlist:**\n{listing}", ephemeral=True)

    @app_commands.command(name="wishclear", description="Clear your entire wishlist")
    async def wishclear(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        count = self.storage.clear_user(user_id)
        if count:
            await interaction.response.send_message(
                f"Cleared **{count}** item(s) from your wishlist.", ephemeral=True
            )
        else:
            await interaction.response.send_message("Your wishlist is already empty.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(WishlistCog(bot, bot.storage))
