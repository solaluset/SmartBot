from discord.ext import commands


@commands.command(usage="say.usage", aliases=("echo",))
async def say(ctx, *, text: str):
    "say.help"
    await ctx.send(text)


def setup(bot):
    bot.add_command(say)
