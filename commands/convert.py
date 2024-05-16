from discord.ext import commands
from modules import embed, num_converter
from modules.i18n import t


MIN_NUM_SYS = 2
MAX_NUM_SYS = 36


@commands.command(usage="convert.usage")
async def convert(ctx, num: str, from_sys: int, to_sys: int):
    "convert.help"
    if not MIN_NUM_SYS <= from_sys <= MAX_NUM_SYS:
        await ctx.send(
            t("convert.invalid_from_sys", ctx.language, min=MIN_NUM_SYS, max=MAX_NUM_SYS)
        )
        return
    if not MIN_NUM_SYS <= to_sys <= MAX_NUM_SYS:
        await ctx.send(
            t("convert.invalid_to_sys", ctx.language, min=MIN_NUM_SYS, max=MAX_NUM_SYS)
        )
        return
    try:
        converted = num_converter.convert_base(num, to_sys, from_sys)
    except ValueError:
        await ctx.send(t("convert.invalid_number", ctx.language))
        return
    em = embed.Embed(
        ctx,
        title=t(
            "convert.result_title",
            ctx.language,
            number=num,
            from_sys=from_sys,
            to_sys=to_sys,
        ),
        description=converted,
    )
    await em.send()


def setup(bot):
    bot.add_command(convert)
