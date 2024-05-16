import discord
from discord.ext import commands
from modules import embed
from modules.i18n import t


@commands.command()
async def invite(ctx):
    "invite.help"
    perms = discord.Permissions(
        add_reactions=True,
        embed_links=True,
        external_emojis=True,
        manage_messages=True,
        read_message_history=True,
        read_messages=True,
        send_messages=True,
        manage_roles=True,
    )
    em = embed.Embed(
        ctx,
        title=t("invite.invites", ctx.language),
        description=t("invite.description", ctx.language),
    )
    em.add_field(
        name=t("invite.bot_link", ctx.language),
        value=discord.utils.oauth_url(ctx.bot.user.id, permissions=perms),
        inline=False,
    )
    if invite := ctx.bot.config.get("support_invite"):
        em.add_field(
            name=t("invite.server_link", ctx.language),
            value=invite,
            inline=False,
        )
    await em.send()


def setup(bot):
    bot.add_command(invite)
