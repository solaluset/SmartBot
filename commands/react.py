import discord
from discord.ext import commands

from modules.i18n import t
from modules.converters import ReactionConverter, SameGuildMessage


@commands.command(usage="react.usage")
@commands.bot_has_permissions(add_reactions=True, read_message_history=True)
async def react(
    ctx, reaction: ReactionConverter, message: SameGuildMessage | None = None
):
    "react.help"
    if not message:
        if ref := ctx.message.reference:
            try:
                message = ref.cached_message or await ctx.fetch_message(ref.message_id)
            except discord.NotFound:
                await ctx.send(t("errors.not_found.message", ctx.language))
                return
        else:
            message = ctx.message
    if not message.channel.permissions_for(ctx.author).add_reactions:
        await ctx.send(t("react.no_perms", ctx.language))
        return
    await message.add_reaction(reaction)


def setup(bot):
    bot.add_command(react)
