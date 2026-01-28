from re import compile

import discord
from discord.ext import commands
from discord.utils import escape_markdown

from modules import permissions, timeparse
from modules.i18n import t

D_ARG = compile(r"(?<!\S)-d\s*(?P<num>.*)$")


@commands.command(usage="ban.usage")
@commands.guild_only()
@commands.has_permissions(ban_members=True)
@commands.bot_has_permissions(ban_members=True)
async def ban(ctx, user: discord.User, *, reason: str | None = None):
    "ban.help"
    if not await permissions.can_operate(ctx, user, t("ban.ban", ctx.language)):
        return
    if reason and (match := D_ARG.search(reason)):
        try:
            days = int(match.group("num"))
        except ValueError:
            return await ctx.send(t("ban.invalid_days", ctx.language))
        reason = D_ARG.sub("", reason)
    else:
        days = 0
    if days < 0 or days > 7:
        return await ctx.send(t("ban.invalid_days_range", ctx.language))
    await ctx.guild.ban(
        user, reason=reason, delete_message_seconds=days * timeparse.MULTIPLIERS["days"]
    )
    await ctx.send(t("ban.user_banned", ctx.language, user=escape_markdown(str(user))))


@commands.command(usage="kick.usage")
@commands.guild_only()
@commands.has_permissions(kick_members=True)
@commands.bot_has_permissions(kick_members=True)
async def kick(ctx, user: discord.Member, *, reason: str | None = None):
    "kick.help"
    if not await permissions.can_operate(ctx, user, t("kick.kick", ctx.language)):
        return
    await user.kick(reason=reason)
    await ctx.send(t("kick.user_kicked", ctx.language, user=escape_markdown(str(user))))


def setup(bot):
    bot.add_command(ban)
    bot.add_command(kick)
