import re
from decimal import Decimal
from urllib.parse import quote

from discord.ext import commands

from modules import embed
from modules.i18n import t

ENDPOINT = "http://api.mathjs.org/v4/?expr="
FLOAT = r"(\d+(\.\d*)?|\.\d+)"
E_PATTERN = re.compile(rf"{FLOAT}e(\+|-)?\d+", re.I)


@commands.command(usage="calc.usage")
async def calc(ctx, *, expr: str):
    "calc.help"
    await ctx.trigger_typing()
    try:
        async with ctx.bot.session.get(ENDPOINT + quote(expr)) as req:
            res = await req.text()
    except Exception:
        return await ctx.send(t("calc.error", ctx.language))
    res = E_PATTERN.sub(lambda m: f"{Decimal(m.group()):f}", res)
    if len(res) > 2000:
        res = res[:1997] + "..."
    em = embed.Embed(ctx, title=t("calc.result", ctx.language), description=res)
    await em.send()


def setup(bot):
    bot.add_command(calc)
