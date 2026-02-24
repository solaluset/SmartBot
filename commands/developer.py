import inspect
from textwrap import TextWrapper

import discord
from discord import Activity, ActivityType, Status
from discord.ext import commands
from discord.ext.pages import Paginator

from modules.utils import execute
from modules.i18n import t


class Splitter(TextWrapper):
    def __init__(self, width: int):
        super().__init__(width, replace_whitespace=False, tabsize=4)

    def _split(self, text: str) -> list[str]:
        return text.splitlines(True)

    def _handle_long_word(
        self,
        reversed_chunks: list[str],
        cur_line: list[str],
        cur_len: int,
        width: int,
    ) -> None:
        # split by words if possible
        split_chunk = super()._split(reversed_chunks.pop())
        split_chunk.reverse()
        reversed_chunks.extend(split_chunk)
        super()._handle_long_word(reversed_chunks, cur_line, cur_len, width)


OUTPUT_FORMAT = "```\n\u200b{}\n```"
_paginate = Splitter(2002 - len(OUTPUT_FORMAT)).wrap


class DeveloperUtils(commands.Cog):
    def __init__(self):
        self._owner_check = commands.is_owner().predicate

    async def cog_check(self, ctx):
        return await self._owner_check(ctx)

    @commands.command(hidden=True)
    async def download(self, ctx, fname: str):
        await ctx.send(file=discord.File(fname))

    @commands.command(hidden=True)
    async def upload(self, ctx, fname: str):
        await ctx.message.attachments[0].save(fname)
        await ctx.send(t("upload.uploaded", ctx.language, name=fname))

    @commands.command(hidden=True)
    async def restart(self, ctx):
        await ctx.send(t("restart.restarting", ctx.language))
        with open("restart", "w") as f:
            if ctx.guild:
                f.write(str(ctx.channel.id))
            else:
                f.write(str(ctx.author.id))
        await ctx.bot.close()

    @commands.command(hidden=True, aliases=("rel",))
    async def reload(self, ctx, command: str):
        old_command = ctx.bot.get_command(command)
        if old_command is None:
            await ctx.send(t("reload.command_not_found", ctx.language))
            return
        if old_command.name == "help":
            module = inspect.getmodule(ctx.bot.help_command).__name__
        else:
            module = old_command.module
        if not module:
            return await ctx.send(t("reload.module_not_found", ctx.language))
        try:
            ctx.bot.reload_extension(module)
        except Exception as e:
            return await ctx.send(t("reload.error", ctx.language, error=e))
        await ctx.send(t("reload.success", ctx.language, command=old_command.name))

    @commands.command(hidden=True)
    async def exec(self, ctx, *, code: str):
        if code.startswith("```"):
            code = code.partition("\n")[2].rstrip("`")
        else:
            code = code.strip("`")
        result = await execute(
            code,
            {
                "bot": ctx.bot,
                "ctx": ctx,
                "discord": discord,
                "commands": commands,
            },
        )

        try:
            last_author = ctx.channel.last_message.author
        except AttributeError:
            last_author = None

        if result and not result.isspace():
            pages = [OUTPUT_FORMAT.format(p) for p in _paginate(result)]
            if len(pages) == 1:
                await ctx.send(pages[0])
            else:
                await Paginator(pages).send(ctx)
        elif last_author != ctx.me:
            await ctx.send(t("exec.completed_without_output", ctx.language))

    @commands.command(hidden=True)
    async def status(
        self,
        ctx,
        name: str,
        type_: int | str = 0,
        status: Status = Status.online,
    ):
        if isinstance(type_, int):
            type_ = ActivityType(type_)
        else:
            type_ = getattr(ActivityType, type_)
        activity = Activity(name=name, type=type_)
        await ctx.bot.change_presence(activity=activity, status=status)

        ctx.bot.config["activity"]["name"] = name
        ctx.bot.config["activity"]["type"] = int(type_)
        ctx.bot.config["status"] = str(status)
        ctx.bot.save_config()

        await ctx.send(t("status.changed", ctx.language))


def setup(bot):
    bot.add_cog(DeveloperUtils())
