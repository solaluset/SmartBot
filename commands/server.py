from discord import utils
from discord.ext import commands
from modules import embed
from modules.i18n import t


@commands.command(aliases=("guild",))
@commands.guild_only()
async def server(ctx):
    "server.help"
    guild = ctx.guild
    res = embed.Embed(
        ctx,
        title=utils.escape_markdown(guild.name),
        description=t("server.description", ctx.language),
    )
    if guild.icon:
        res.set_image(url=guild.icon.url)
    res.add_field(name=t("server.id", ctx.language), value=guild.id, inline=False)
    res.add_field(
        name=t("server.created", ctx.language),
        value=t(
            "server.created_ago",
            ctx.language,
            time=f"<t:{int(guild.created_at.timestamp())}:F>",
            count=(utils.utcnow() - guild.created_at).days,
        ),
        inline=False,
    )
    res.add_field(
        name=t("server.owner", ctx.language),
        value=utils.escape_markdown(str(guild.owner)),
        inline=False,
    )
    res.add_field(
        name=t("server.member_count", ctx.language),
        value=guild.member_count,
        inline=False,
    )

    await res.send()


def setup(bot):
    bot.add_command(server)
