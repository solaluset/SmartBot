import asyncio

from discord import Message, User
from discord.ext import commands
from discord.utils import escape_markdown
from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import insert

from modules.i18n import t
from modules.regexps import ID
from modules.db import WrappedTable
from modules.TicTacToe import MAX_FIELD_SIZE, MAX_GAMERS, TicTacToe, UltimateTicTacToe
from modules.converters import SmartUserConverter


ttt_table = WrappedTable(
    "ttt_stats",
    None,
    Column("user_id", String(25), primary_key=True),
    Column("total_games", Integer, nullable=False),
    Column("won_games", Integer, nullable=False),
)


class TicTac(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tictac_sessions = {}
        self.stats_table = ttt_table
        self.stats_table.engine = bot.sql

    @commands.group(
        usage="tictac.usage",
        aliases=("tictactoe", "ttt"),
        invoke_without_command=True,
    )
    async def tictac(
        self,
        ctx,
        gamers: commands.Greedy[User],
        size: int = 3,
        combo: int = 3,
        ephemeral_threshold: int = 0,
        mode: str = "",
    ):
        "tictac.help"
        curr_sess = self.tictac_sessions.get(ctx.channel.id, None)
        if curr_sess is not None:
            await ctx.send(t("tictac.already_playing", ctx.language))
            return

        if not gamers:
            await ctx.send(t("tictac.missing_opponent", ctx.language))
            return
        gamers = [user.mention for user in [ctx.author] + gamers]
        use_ai = ctx.me.mention in gamers
        if size < 1 or combo < 1:
            await ctx.send(t("tictac.negative_specs", ctx.language))
            return
        if size > MAX_FIELD_SIZE:
            await ctx.send(t("tictac.field_too_big", ctx.language, limit=MAX_FIELD_SIZE))
            return
        if combo > size:
            await ctx.send(t("tictac.line_too_big", ctx.language))
            return
        if len(gamers) > MAX_GAMERS:
            await ctx.send(t("tictac.too_many_gamers", ctx.language))
            return

        curr_sess = (UltimateTicTacToe if mode == "ULTIMATE" else TicTacToe)(
            await ctx.send(t("tictac.game_started", ctx.language)),
            size,
            combo,
            *gamers,
            use_ai=use_ai,
            language=ctx.language,
            ephemeral_threshold=max(0, ephemeral_threshold),
        )

        self.tictac_sessions[ctx.channel.id] = curr_sess
        await asyncio.sleep(1)
        await curr_sess.resend()

    async def _stop(self, id: int):
        curr_sess = self.tictac_sessions.pop(id)
        curr_sess.stop()
        await curr_sess.resend()

    @tictac.command()
    async def stop(self, ctx):
        "tictac.stop.help"
        curr_sess = self.tictac_sessions.get(ctx.channel.id, None)
        if curr_sess is None:
            return
        if (
            ctx.author.mention not in curr_sess.gamers
            and not ctx.channel.permissions_for(ctx.author).manage_server
        ):
            await ctx.send(t("tictac.stop.cant_stop", ctx.language), delete_after=5.0)
        else:
            await self._stop(ctx.channel.id)

    @tictac.command(usage="tictac.stats.usage")
    async def stats(self, ctx, user: SmartUserConverter = None):
        "tictac.stats.help"
        user = user or ctx.author
        data = await self.stats_table.select(
            "total_games", "won_games", user_id=str(user.id)
        )
        if data:
            total, won = data[0]
        else:
            total, won = 0, 0
        await ctx.send(
            t(
                "tictac.stats.stats",
                ctx.language,
                user=escape_markdown(str(user)),
                total=total,
                won=won,
                percent=round(won / (total or 1) * 100),
            )
        )

    async def update_stats(self, gamers: list[str], winner: str | None):
        async with self.bot.sql.begin() as conn:
            await conn.execute(
                insert(self.stats_table.table).on_conflict_do_update(
                    constraint=self.stats_table.table.primary_key,
                    set_={
                        "total_games": self.stats_table.table.c.total_games + 1,
                        "won_games": self.stats_table.table.c.won_games
                        + (self.stats_table.table.c.user_id == winner).cast(Integer),
                    },
                ),
                [
                    {"user_id": g, "total_games": 1, "won_games": int(g == winner)}
                    for g in gamers
                ],
            )

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        curr_sess = self.tictac_sessions.get(message.channel.id, None)
        if (
            not curr_sess
            or message.author.mention != curr_sess.gamers[curr_sess.turn_of]
        ):
            return
        if not curr_sess.update(message.content):
            return
        if curr_sess.winner is None:
            await curr_sess.resend()
        else:
            # update stats only if game was "fair"
            if (
                curr_sess.to_win >= 4
                or curr_sess.to_win == 3
                and len(curr_sess.table) == 3
            ):
                gamers = [ID.search(g).group() for g in curr_sess.gamers]
                winner = (
                    ID.search(curr_sess.winner).group() if curr_sess.winner else None
                )
                await self.update_stats(gamers, winner)
            await self._stop(message.channel.id)


def setup(bot):
    bot.add_cog(TicTac(bot))
