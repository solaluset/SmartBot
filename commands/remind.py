import re
import logging
from asyncio import gather
from datetime import datetime, timezone

from discord import DMChannel, Forbidden, NotFound
from discord.ext import commands, tasks
from sqlalchemy import Column, Float, String

from modules.db import WrappedTable
from modules.i18n import t
from modules.embed import Embed
from modules.regexps import QUOTED_PATTERN
from modules.SmartBot import REMOVE_ALIASES
from modules.timeparse import TIMEFORMATS, timeparse

MAX_REMINDER_LEN = 1000
reminders_table = WrappedTable(
    "reminders",
    None,
    Column("requester_id", String(25), nullable=False),
    Column("channel_id", String(25), nullable=False),
    Column("time", Float, nullable=False),
    Column("subject", String(MAX_REMINDER_LEN), nullable=False),
)
PATTERNS = [re.compile(f + r"(?!\S)", re.I) for f in TIMEFORMATS]
PATTERNS.append(re.compile(QUOTED_PATTERN))


class Remind(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = reminders_table
        self.data.engine = bot.sql
        self.sender_loop.start()

    def cog_unload(self):
        self.sender_loop.stop()

    @staticmethod
    def _try_isoformat(text: str, split_n: int) -> tuple[float, str] | None:
        parts = text.split(None, split_n)
        if len(parts) > split_n:
            rest = parts.pop()
        else:
            rest = ""
        time = " ".join(parts)
        if "+" in time and ":" not in time.split("+")[-1]:
            time += ":00"
        try:
            return datetime.fromisoformat(time).timestamp(), rest
        except ValueError:
            return None

    @classmethod
    def parse_timestamp(cls, text: str) -> tuple[float | None, str]:
        result = cls._try_isoformat(text, 2) or cls._try_isoformat(text, 1)
        if result:
            return result
        for p in PATTERNS:
            match = p.match(text)
            if match:
                g = match.group()
                return (
                    datetime.now(timezone.utc).timestamp() + timeparse(g.strip('"')),
                    text.replace(g, "", 1).strip(),
                )
        return None, text

    @commands.group(usage="remind.usage", invoke_without_command=True)
    async def remind(self, ctx, *, subject: str):
        "remind.help"
        timestamp, subject = self.parse_timestamp(subject)
        if timestamp is None or not subject:
            await ctx.send(t("remind.invalid_args", ctx.language))
            return
        elif len(subject) > MAX_REMINDER_LEN:
            await ctx.send(
                t("remind.max_length_reached", ctx.language, limit=MAX_REMINDER_LEN)
            )
            return
        await self.data.insert(
            requester_id=str(ctx.author.id),
            channel_id=str(ctx.channel.id),
            time=timestamp,
            subject=subject,
        )
        await ctx.send(t("remind.created", ctx.language, time=f"<t:{int(timestamp)}:R>"))

    @remind.command()
    async def list(self, ctx):
        "remind.list.help"
        async with self.bot.sql.connect() as conn:
            reminds = await conn.execute(
                self.data.table.select()
                .where(self.data.table.c.requester_id == str(ctx.author.id))
                .where(self.data.table.c.channel_id == str(ctx.channel.id))
                .order_by(self.data.table.c.time)
            )
            reminds = reminds.all()
        em = Embed(
            ctx,
            title=t("remind.list.title", ctx.language),
            description=t("remind.list.empty", ctx.language) if not reminds else "",
        )
        for i, (_, _, time, subject) in enumerate(reminds, 1):
            em.add_field(
                name=f"{i} - <t:{int(time)}:F>",
                value=subject,
                inline=False,
            )
        await em.send()

    @remind.command(usage="remind.remove.usage", aliases=REMOVE_ALIASES)
    async def remove(self, ctx, num: int):
        "remind.remove.help"
        async with self.bot.sql.connect() as conn:
            reminds = await conn.execute(
                self.data.table.select()
                .where(self.data.table.c.requester_id == str(ctx.author.id))
                .where(self.data.table.c.channel_id == str(ctx.channel.id))
                .order_by(self.data.table.c.time)
            )
            reminds = reminds.all()
        if num < 1 or num > len(reminds):
            return await ctx.send(t("remind.remove.invalid_number", ctx.language))
        _, _, time, reminder = reminds[num - 1]
        await self.data.delete(
            requester_id=str(ctx.author.id),
            channel_id=str(ctx.channel.id),
            time=time,
            subject=reminder,
        )
        await ctx.send(t("remind.remove.removed", ctx.language, reminder=reminder))

    @remind.command()
    async def clear(self, ctx):
        "remind.clear.help"
        bot_msg = await ctx.send(t("remind.clear.ask", ctx.language))
        try:
            msg = await ctx.bot.wait_for(
                "message",
                check=lambda m: m.channel == ctx.channel and m.author == ctx.author,
                timeout=30,
            )
        except TimeoutError:
            msg = None
        if not msg or msg.content != t("remind.clear.confirm", ctx.language):
            await bot_msg.edit(t("remind.clear.cancelled", ctx.language))
            return
        await self.data.delete(
            requester_id=str(ctx.author.id),
            channel_id=str(ctx.channel.id),
        )
        await ctx.send(t("remind.clear.cleared", ctx.language))

    @tasks.loop(minutes=0.5)
    async def sender_loop(self):
        time = datetime.now(timezone.utc).timestamp()
        if self.bot.test_mode:
            condition = self.data.table.c.channel_id == str(self.bot.test_channel_id)
        else:
            condition = self.data.table.c.channel_id != str(self.bot.test_channel_id)
        try:
            async with self.bot.sql.begin() as conn:
                reminders = await conn.execute(
                    self.data.table.delete()
                    .returning(
                        self.data.table.c.requester_id,
                        self.data.table.c.channel_id,
                        self.data.table.c.subject,
                    )
                    .where(self.data.table.c.time <= time)
                    .where(condition)
                )
                reminders = reminders.all()
        except Exception as e:
            logging.error(f"Failed to fetch reminders: {e}")
            return
        await gather(
            *(
                self.send_reminder(int(user_id), int(channel_id), subject)
                for user_id, channel_id, subject in reminders
            )
        )

    @sender_loop.before_loop
    async def wait(self):
        await self.bot.wait_until_ready()

    async def send_reminder(self, user_id: int, channel_id: int, subject: str):
        try:
            target = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(
                channel_id
            )
        except NotFound:
            target = None
        guild = getattr(target, "guild", None)
        language = await self.bot.get_language(guild)
        if guild and target and not target.permissions_for(guild.me).send_messages:
            # will error anyway, don't even try
            target = None
        try:
            await target.send(
                t(
                    "remind.message",
                    language,
                    user=f"<@{user_id}>",
                    subject=subject,
                )
            )
        except Exception as e:
            if not isinstance(e, (Forbidden, AttributeError)):
                logging.error(f"Error while trying to send reminder: {e}")
            if isinstance(target, DMChannel):
                return
            if channel := await self.get_dm_channel(user_id):
                return await self.send_reminder(user_id, channel.id, subject)

    async def get_dm_channel(self, user_id: int) -> DMChannel | None:
        try:
            user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
        except NotFound:
            return None
        return await user.create_dm()


def setup(bot):
    bot.add_cog(Remind(bot))
