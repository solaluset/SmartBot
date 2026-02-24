import inspect

import discord
from discord import Activity, ActivityType, Status
from discord.ext import commands

from modules.utils import execute
from modules.i18n import t


class OwnerUtils(commands.Cog):
    @commands.command(hidden=True)
    @commands.is_owner()
    async def download(self, ctx, fname: str):
        await ctx.send(file=discord.File(fname))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def upload(self, ctx, fname: str):
        await ctx.message.attachments[0].save(fname)
        await ctx.send(t("upload.uploaded", ctx.language, name=fname))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def restart(self, ctx):
        await ctx.send(t("restart.restarting", ctx.language))
        with open("restart", "w") as f:
            if ctx.guild:
                f.write(str(ctx.channel.id))
            else:
                f.write(str(ctx.author.id))
        await ctx.bot.close()

    @commands.command(hidden=True, aliases=("rel",))
    @commands.is_owner()
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
    @commands.is_owner()
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
            await ctx.send(f"```\n{result}```")
        elif last_author != ctx.me:
            await ctx.send(t("exec.completed_without_output", ctx.language))

    @commands.command(hidden=True)
    @commands.is_owner()
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
    bot.add_cog(OwnerUtils())
