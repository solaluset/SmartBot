import discord
from discord.ext import commands
from modules import embed
from modules.i18n import t, generate_name_localizations


ENG = "`qwertyuiop[]\\asdfghjkl;'zxcvbnm,./@#$^&QWERTYUIOP{}|ASDFGHJKL:\"ZXCVBNM<>?"
UKR = "'йцукенгшщзхїґфівапролджєячсмитьбю.\"№;:?ЙЦУКЕНГШЩЗХЇҐФІВАПРОЛДЖЄЯЧСМИТЬБЮ,"
TR = str.maketrans(UKR + ENG, ENG + UKR)


async def _text_from_message(message: discord.Message | discord.ForwardedMessage) -> str:
    if message.content or isinstance(message, discord.ForwardedMessage):
        return message.content

    if message.snapshots:
        return await _text_from_message(message.snapshots[0].message)

    if ref := message.reference:
        try:
            return (
                ref.cached_message or await message.channel.fetch_message(ref.message_id)
            ).content
        except discord.Forbidden:
            return ""

    return ""


@commands.command(usage="layout.usage", aliases=("lo",))
async def layout(ctx, *, text: str | None = None):
    "layout.help"
    if not text:
        try:
            text = await _text_from_message(ctx.message)
        except discord.NotFound:
            return await ctx.send(t("errors.not_found.message", ctx.language))
    if not text:
        return await ctx.send(t("layout.missing_text", ctx.language))
    em = embed.Embed(
        ctx,
        title=t("layout.title", ctx.language),
        description=text.translate(TR),
    )
    await em.send()


@commands.message_command(
    name="layout",
    name_localizations=generate_name_localizations("layout.title"),
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    },
)
async def layout_message(ctx, message: discord.Message):
    try:
        text = await _text_from_message(message)
    except discord.NotFound:
        return await ctx.respond(
            t("errors.not_found.message", ctx.language), ephemeral=True
        )
    if not text:
        return await ctx.respond(t("layout.missing_text", ctx.language), ephemeral=True)
    em = embed.Embed(
        ctx,
        title=t("layout.title", ctx.language),
        description=text.translate(TR),
    )
    await em.send(ephemeral=True)


def setup(bot):
    bot.add_command(layout)
    bot.add_application_command(layout_message)
