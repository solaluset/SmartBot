from discord.ext import commands
from modules.i18n import AVAILABLE_LANGUAGES, t


@commands.command(usage="language.usage")
@commands.guild_only()
@commands.has_permissions(manage_guild=True)
async def language(ctx, lang: str | None = None):
    "language.help"
    if not lang:
        return await ctx.send(t("language.current", ctx.language))
    lang = lang.lower()
    if lang not in AVAILABLE_LANGUAGES:
        return await ctx.send(
            t(
                "language.unavailable",
                ctx.language,
                languages=", ".join(AVAILABLE_LANGUAGES),
            )
        )
    await ctx.bot.guilds_data.upsert(
        guild_id=str(ctx.guild.id),
        language=lang,
    )
    await ctx.bot.get_language.delete(ctx.guild)
    await ctx.send(t("language.switched", lang))


def setup(bot):
    bot.add_command(language)
