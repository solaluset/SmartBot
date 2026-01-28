from textwrap import TextWrapper

from discord.ext import commands

from modules import embed

MAX_TITLE_SIZE = 256
wrap = TextWrapper(MAX_TITLE_SIZE).wrap


@commands.command(usage="poll.usage", aliases=("voting",))
@commands.guild_only()
async def poll(ctx, *, text: str):
    "poll.help"
    title, _, text = text.partition("\n")
    wrapped_title = wrap(title)[0]
    description = title.replace(wrapped_title, "", 1) + "\n" + text
    em = embed.Embed(ctx, title=wrapped_title, description=description)
    em.set_footer(text=ctx.author, icon_url=ctx.author.display_avatar)

    message = await em.send()

    reactions = text.splitlines()
    if not reactions:
        reactions = ["👍", "👎"]
    for entry in reactions:
        try:
            await message.add_reaction(entry.split(None, 1)[0])
        except Exception:
            pass


def setup(bot):
    bot.add_command(poll)
