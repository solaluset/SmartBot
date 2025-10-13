from string import ascii_uppercase
from typing import Awaitable, Callable

from discord import Interaction
from discord.ui import Button, View

from . import TicTacToe
from .scores import EMPTY


class TTTView(View):
    def __init__(self, ttt: TicTacToe, update_callback: Callable[[], Awaitable]):
        super().__init__(timeout=300)
        self.ttt = ttt
        self.update_callback = update_callback

    async def interaction_check(self, inter) -> bool:
        return inter.user.mention == self.ttt.get_current_player()

    async def on_check_failure(self, inter):
        await inter.response.send_message("Not your move.", ephemeral=True)

    async def on_timeout(self):
        await self.update_callback()


class CellButton(Button):
    def __init__(self, x: int, y: int, enabled: bool):
        super().__init__(
            label=f"{ascii_uppercase[y]}{x + 1}", row=x, disabled=not enabled
        )

    async def callback(self, inter: Interaction):
        await inter.response.defer()
        self.view.ttt.update(self.label)
        await self.view.update_callback()


def build_view(session: TicTacToe, callback: Callable[[], Awaitable]) -> TTTView | None:
    if session.winner or session.draw or session.stopped:
        return None
    view = TTTView(session, callback)
    board = session.get_active_board()
    if len(board) <= 5:
        for x, row in enumerate(board):
            for y, cell in enumerate(row):
                view.add_item(CellButton(x, y, cell == EMPTY))
    return view
