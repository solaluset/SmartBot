from re import compile

from discord import Member
from discord.ext import commands

from modules.i18n import t


S_ARG = compile(r"(?<!\S)-s$")


@commands.command(usage="clean.usage", aliases=("purge",))
@commands.bot_has_permissions(manage_messages=True, read_message_history=True)
async def clean(ctx, amount: int, user: Member | None, *, reason: str | None = None):
    "clean.help"
    if reason:
        silent = bool(S_ARG.search(reason))
        reason = S_ARG.sub("", reason)
    else:
        silent = False

    if (
        user != ctx.author
        and not ctx.channel.permissions_for(ctx.author).manage_messages
    ):
        return await ctx.send(t("clean.missing_permissions", ctx.language))

    if user:

        def check(message):
            return message.author == user

    else:

        def check(message):
            return True

    count = len(await ctx.channel.purge(limit=amount, check=check, reason=reason))
    if not silent:
        await ctx.send(t("clean.messages_deleted", ctx.language, count=count))


def setup(bot):
    bot.add_command(clean)
