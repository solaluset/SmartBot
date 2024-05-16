import random
from discord.ext import commands
from modules.i18n import t


@commands.command(usage="choose.usage")
async def choose(ctx, *, variants: str):
    "choose.help"
    await ctx.send(
        t(
            "choose.answer",
            ctx.language,
            user=ctx.author.mention,
            answer=random.choice(variants.split("/")),
        )
    )


def setup(bot):
    bot.add_command(choose)
