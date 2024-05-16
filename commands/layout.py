import discord
from discord.ext import commands
from modules import embed
from modules.i18n import t


ENG = "`qwertyuiop[]\\asdfghjkl;'zxcvbnm,./@#$^&QWERTYUIOP{}|ASDFGHJKL:\"ZXCVBNM<>?"
UKR = "'йцукенгшщзхїґфівапролджєячсмитьбю.\"№;:?ЙЦУКЕНГШЩЗХЇҐФІВАПРОЛДЖЄЯЧСМИТЬБЮ,"
TR = str.maketrans(UKR + ENG, ENG + UKR)


@commands.command(usage="layout.usage", aliases=("lo",))
async def layout(ctx, *, text: str | None = None):
    "layout.help"
    if not text and (ref := ctx.message.reference):
        try:
            text = (
                ref.cached_message or await ctx.fetch_message(ref.message_id)
            ).content
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


def setup(bot):
    bot.add_command(layout)
