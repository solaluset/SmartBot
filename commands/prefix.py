from discord.ext import commands
from modules.prima import MAX_PREFIX_LEN, ADD_ALIASES, REMOVE_ALIASES
from modules.i18n import t

MAX_PREFIXES_PER_GUILD = 5


@commands.group(usage="prefix.usage", invoke_without_command=True)
@commands.guild_only()
async def prefix(ctx):
    "prefix.help"
    await ctx.send(await ctx.bot.get_prefixes_string(ctx.guild))


@prefix.command(usage="prefix.add.usage", aliases=ADD_ALIASES)
@commands.has_permissions(manage_guild=True)
async def add(ctx, *, prefix_arg: str):
    "prefix.add.help"
    if len(prefix_arg) > MAX_PREFIX_LEN:
        await ctx.send(t("prefix.add.too_long", ctx.language))
        return
    if prefix_arg in await ctx.bot.get_prefixes(ctx.guild):
        await ctx.send(t("prefix.add.already_exists", ctx.language, prefix=prefix_arg))
        return
    custom_prefixes = await ctx.bot.get_prefixes(ctx.guild, False)
    if len(custom_prefixes) >= MAX_PREFIXES_PER_GUILD:
        await ctx.send(
            t("prefix.add.limit_reached", ctx.language, limit=MAX_PREFIXES_PER_GUILD)
        )
        return
    custom_prefixes.append(prefix_arg)
    custom_prefixes.sort(key=len, reverse=True)
    await ctx.bot.guilds_data.upsert(
        guild_id=str(ctx.guild.id),
        prefixes=custom_prefixes,
    )
    await ctx.bot.get_prefixes.delete(ctx.guild)
    await ctx.bot.get_prefixes.delete(ctx.guild, False)
    await ctx.send(t("prefix.add.added", ctx.language, prefix=prefix_arg))


@prefix.command(usage="prefix.remove.usage", aliases=REMOVE_ALIASES)
@commands.has_permissions(manage_guild=True)
async def remove(ctx, *, prefix_arg: str):
    "prefix.remove.help"
    custom_prefixes = await ctx.bot.get_prefixes(ctx.guild, False)
    if not custom_prefixes:
        await ctx.send(t("prefix.remove.no_prefixes", ctx.language))
        return
    if prefix_arg not in custom_prefixes:
        await ctx.send(t("prefix.remove.not_found", ctx.language, prefix=prefix_arg))
        return
    custom_prefixes.remove(prefix_arg)
    await ctx.bot.guilds_data.upsert(
        guild_id=str(ctx.guild.id),
        prefixes=custom_prefixes,
    )
    await ctx.bot.get_prefixes.delete(ctx.guild)
    await ctx.bot.get_prefixes.delete(ctx.guild, False)
    await ctx.send(t("prefix.remove.removed", ctx.language, prefix=prefix_arg))


def setup(bot):
    bot.add_command(prefix)
