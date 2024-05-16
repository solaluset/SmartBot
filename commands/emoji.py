from discord import Asset
from discord.ext import commands
from discord.ext.commands import EmojiNotFound

from modules.i18n import t
from modules.regexps import ID
from modules.converters import SmartEmojiConverter


@commands.command(usage="emoji.usage")
async def emoji(ctx, em: SmartEmojiConverter):
    "emoji.help"
    await ctx.send(em)


@commands.command(usage="emoji.usage")
async def get_emoji(ctx, emoji: str):
    "get_emoji.help"
    try:
        emoji = await SmartEmojiConverter().convert(ctx, emoji)
    except EmojiNotFound:
        pass
    else:
        return await ctx.send(emoji.url)
    id = ID.findall(emoji)
    if id:
        fmt = "gif" if emoji.startswith("<a:") else "png"
        return await ctx.send(f"{Asset.BASE}/emojis/{id[-1]}.{fmt}")
    await ctx.send(t("errors.not_found.emoji", ctx.language))


def setup(bot):
    bot.add_command(emoji)
    bot.add_command(get_emoji)
