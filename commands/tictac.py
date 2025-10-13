from discord import Message, User
from discord.ext import commands
from discord.utils import escape_markdown
from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import insert

from modules.i18n import t
from modules.regexps import ID
from modules.db import WrappedTable
from modules.TicTacToe import MAX_FIELD_SIZE, MAX_PLAYERS, TicTacToe, UltimateTicTacToe
from modules.TicTacToe.discord import build_view
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
        if size < 1 or combo < 1:
            await ctx.send(t("tictac.negative_specs", ctx.language))
            return
        if size > MAX_FIELD_SIZE:
            await ctx.send(t("tictac.field_too_big", ctx.language, limit=MAX_FIELD_SIZE))
            return
        if combo > size:
            await ctx.send(t("tictac.line_too_big", ctx.language))
            return
        if len(gamers) > MAX_PLAYERS:
            await ctx.send(t("tictac.too_many_gamers", ctx.language))
            return

        curr_sess = (UltimateTicTacToe if mode == "ULTIMATE" else TicTacToe)(
            size,
            combo,
            gamers,
            ctx.language,
            ai_players=[ctx.me.mention],
            ephemeral_threshold=max(0, ephemeral_threshold),
        )
        if len(str(curr_sess)) > 2000:
            return await ctx.send(t("tictac.message-too-big", ctx.language))

        self.tictac_sessions[ctx.channel.id] = (
            await ctx.send(**self._build_message(ctx.channel.id, curr_sess)),
            curr_sess,
        )

    async def _update(self, channel_id: int, resend: bool = False):
        data = self.tictac_sessions.get(channel_id)
        if not data:
            return
        message, session = data
        if resend:
            await message.delete()
            message = await message.channel.send(
                **self._build_message(channel_id, session)
            )
        else:
            await message.edit(**self._build_message(channel_id, session))
        if session.winner or session.draw or session.stopped:
            del self.tictac_sessions[channel_id]
            if session.stopped:
                return
            # update stats only if game was "fair"
            if (
                session.win_size >= 4
                or session.win_size == 3
                and len(session.board) == 3
            ):
                players = [ID.search(p).group() for p in session.players]
                winner = ID.search(session.winner).group() if session.winner else None
                await self.update_stats(players, winner)
        else:
            self.tictac_sessions[channel_id] = (message, session)

    def _build_message(self, channel_id: int, session: TicTacToe) -> dict:
        return {
            "content": session,
            "view": build_view(session, lambda: self._update(channel_id)),
        }

    @tictac.command()
    async def stop(self, ctx):
        "tictac.stop.help"
        curr_sess = self.tictac_sessions.get(ctx.channel.id, None)
        if curr_sess is None:
            return
        curr_sess = curr_sess[1]
        if (
            ctx.author.mention not in curr_sess.players
            and not ctx.channel.permissions_for(ctx.author).manage_server
        ):
            await ctx.send(t("tictac.stop.cant_stop", ctx.language), delete_after=5.0)
        else:
            curr_sess.stop()
            await self._update(ctx.channel.id, True)

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
        if curr_sess is None:
            return
        game_message, session = curr_sess
        if message.author.mention != session.get_current_player():
            return
        if not session.update(message.content):
            return
        await self._update(message.channel.id, True)


def setup(bot):
    bot.add_cog(TicTac(bot))
