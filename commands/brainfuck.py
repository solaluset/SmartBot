from i18n import t
from discord.ext import commands

from modules.brainfuck import BFException, State, parse


MAX_OPS = 10_000


@commands.command(usage="brainfuck.usage", aliases=("bf",))
async def brainfuck(ctx, *, code: str):
    "brainfuck.help"
    if code.startswith("```"):
        code = code.partition("\n")[2]
        code, _, input_ = code.partition("```\n")
    else:
        input_ = ""
    state = State(input_.encode(), MAX_OPS)
    try:
        state.interpret(parse(code))
    except BFException as e:
        await ctx.send(t("brainfuck.error", ctx.language, error=e))
    else:
        await ctx.send(t("brainfuck.result", ctx.language, result=state.output.decode()))


def setup(bot):
    bot.add_command(brainfuck)
