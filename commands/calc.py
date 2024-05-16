from urllib.request import quote
from discord.ext import commands
from modules import embed
from modules.i18n import t


ENDPOINT = "http://api.mathjs.org/v4/?expr="


@commands.command(usage="calc.usage")
async def calc(ctx, *, expr: str):
    "calc.help"
    await ctx.trigger_typing()
    try:
        async with ctx.bot.session.get(ENDPOINT + quote(expr)) as req:
            res = await req.text()
    except Exception:
        res = t("calc.error", ctx.language)
    em = embed.Embed(ctx, title=t("calc.result", ctx.language), description=res)
    await em.send()


def setup(bot):
    bot.add_command(calc)
