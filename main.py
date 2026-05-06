"""
Entry point for the Fortnite Item Shop Discord bot.

Loads environment variables, configures logging, validates that the
Discord token is set, and starts the bot.

Usage:
    python main.py

Requires:
    A .env file in the project root with DISCORD_TOKEN set.
"""

import logging
import os
import sys

from dotenv import load_dotenv

from bot.bot import ItemShopBot

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    sys.exit("DISCORD_TOKEN is not set in .env")

FORTNITE_API_KEY = os.environ.get("FORTNITE_API_KEY")
if not FORTNITE_API_KEY:
    sys.exit("FORTNITE_API_KEY is not set in .env")

_channel_id = os.environ.get("SHOP_CHANNEL_ID")
if not _channel_id:
    sys.exit("SHOP_CHANNEL_ID is not set in .env")
SHOP_CHANNEL_ID = int(_channel_id)

WISHLIST_FILE = "wishlist.json"

bot = ItemShopBot(
    channel_id=SHOP_CHANNEL_ID,
    wishlist_path=WISHLIST_FILE,
    fortnite_api_key=FORTNITE_API_KEY,
)
bot.run(DISCORD_TOKEN, log_handler=None)
