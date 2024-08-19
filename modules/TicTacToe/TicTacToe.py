from string import ascii_lowercase, ascii_uppercase
from typing import TYPE_CHECKING

from modules.i18n import t
from .scores import EMPTY, Scores

if TYPE_CHECKING:
    from discord import Message


MAX_FIELD_SIZE = len(ascii_uppercase)
SIGNS = list(ascii_lowercase)
for redef_sign in reversed(("x", "o")):
    SIGNS.remove(redef_sign)
    SIGNS.insert(0, redef_sign)
del redef_sign
SIGNS = tuple(SIGNS)
MAX_GAMERS = len(SIGNS)


class TicTacToe:
    def __init__(
        self,
        message: "Message",
        size: int,
        combo_to_win: int,
        *gamers: str,
        use_ai=False,
        language="en",
    ):
        self.message = message
        self.gamers = gamers
        self.use_ai = use_ai
        self.language = language
        self.signs = SIGNS[: len(gamers)]
        if len(self.signs) != len(self.gamers):
            raise ValueError("Too many gamers.")
        self.turn_of = 0
        self.winner = None
        self.table = [[EMPTY] * size]
        for _ in range(1, size):
            self.table.append(self.table[0].copy())
        self.to_win = combo_to_win
        self.stopped = False

    async def resend(self):
        await self.message.delete()
        self.message = await self.message.channel.send(self)

    def update(self, user_input: str) -> bool:
        if not user_input:
            return False
        user_input = user_input.replace("-", "").replace(" ", "").upper()
        if user_input[0] in ascii_uppercase:
            letter = user_input[0]
            user_input = user_input[1:]
        elif user_input[-1] in ascii_uppercase:
            letter = user_input[-1]
            user_input = user_input[:-1]
        else:
            return False
        try:
            number = int(user_input) - 1
        except ValueError:
            return False
        letter = ord(letter) - ord("A")
        if letter >= len(self.table) or number not in range(len(self.table)):
            return False
        return self._update(number, letter)

    def _update(self, x: int, y: int) -> bool:
        if self.table[x][y] != EMPTY:
            return False
        self.table[x][y] = self.signs[self.turn_of]
        if self.check_win():
            self.winner = self.gamers[self.turn_of]
            return True
        if self.check_draw():
            self.winner = False
            return True
        self.turn_of += 1
        if self.turn_of == len(self.gamers):
            self.turn_of = 0
        if self.use_ai and self.message.author.mention == self.gamers[self.turn_of]:
            return self._update(
                *Scores(self.table, self.to_win).get_move(self.signs[self.turn_of])
            )
        return True

    def check_draw(self) -> bool:
        for i in self.table:
            for j in i:
                if j == EMPTY:
                    return False
        return True

    def check_win(self) -> bool:
        score = max(Scores(self.table, self.to_win), key=lambda x: x.score)
        if score.score >= self.to_win:
            for i, j in score.iter_cells():
                self.table[i][j] = self.table[i][j].upper()
            return True
        return False

    def stop(self):
        if self.winner is None:
            self.stopped = True

    def __str__(self):
        return (
            " vs ".join(self.gamers)
            + "\n"
            + self.table_str()
            + "\n"
            + self.signature_str()
        )

    def table_str(self) -> str:
        max_len = len(str(len(self.table))) + 1
        text = (
            "```\n\u200b"
            + " " * max_len
            + " ".join(ascii_uppercase[: len(self.table)])
            + "\n"
        )
        for i, row in enumerate(self.table, 1):
            text += str(i).ljust(max_len) + " ".join(row) + "\n"
        return text + "```"

    def signature_str(self) -> str:
        if self.stopped:
            return t("tictac.stop.stopped", self.language)
        elif self.winner is None:
            return t(
                "tictac.current_player",
                self.language,
                player=self.gamers[self.turn_of],
            )
        elif self.winner:
            return t("tictac.winner", self.language, winner=self.winner)
        else:
            return t("tictac.draw", self.language)
