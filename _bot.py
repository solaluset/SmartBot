import sys
import logging as log

import discord

from modules.SmartBot import SmartBot
from modules.i18n import init as init_i18n


log.basicConfig(
    level=log.WARNING,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[log.FileHandler("log.txt"), log.StreamHandler()],
)

log.info("Configuring the bot...")

init_i18n()

bot = SmartBot(
    description="bot_description",
    intents=discord.Intents.all(),
    allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True),
    test_mode="--test" in sys.argv,
)


bot.load_extensions(
    "alias",
    "autorole",
    "ban",
    "brainfuck",
    "calc",
    "choose",
    "clean",
    "convert",
    "emoji",
    "for_owner",
    "help",
    "invite",
    "language",
    "layout",
    "poll",
    "prefix",
    "react",
    "reactionrole",
    "remind",
    "say",
    "server",
    "tictac",
    "user",
    package="commands",
)


if __name__ == "__main__":
    log.info("Connecting...")
    try:
        bot.run()
    except RuntimeError as e:
        if e.args != ("Session is closed",):
            raise
    log.info("Stopped.")
