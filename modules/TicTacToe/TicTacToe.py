from collections import defaultdict
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
EPHEMERENESS_SYMBOL = "\u036f"


class TicTacToe:
    def __init__(
        self,
        message: "Message",
        size: int,
        combo_to_win: int,
        *gamers: str,
        use_ai=False,
        language="en",
        ephemeral_threshold=0,
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
        self.move_history = defaultdict(list)
        self.ephemeral_threshold = ephemeral_threshold
        self.stopped = False

    async def resend(self):
        await self.message.delete()
        self.message = await self.message.channel.send(self)

    def _parse_cell(self, user_input: str) -> tuple[int, int] | None:
        if not user_input:
            return None
        user_input = user_input.replace("-", "").replace(" ", "").upper()
        if user_input[0] in ascii_uppercase:
            letter = user_input[0]
            user_input = user_input[1:]
        elif user_input[-1] in ascii_uppercase:
            letter = user_input[-1]
            user_input = user_input[:-1]
        else:
            return None
        try:
            number = int(user_input) - 1
        except ValueError:
            return None
        letter = ord(letter) - ord("A")
        if letter >= len(self.table) or number not in range(len(self.table)):
            return None
        return number, letter

    def update(self, user_input: str) -> bool:
        coords = self._parse_cell(user_input)
        if coords is None:
            return False
        return self._update(coords[0], coords[1])

    def _update(self, x: int, y: int) -> bool:
        if self.table[x][y] != EMPTY:
            return False
        sign = self.signs[self.turn_of]
        if (
            self.ephemeral_threshold
            and len(self.move_history[sign]) == self.ephemeral_threshold
        ):
            ephemeral = self.move_history[sign].pop(0)
            self._handle_ephemereness(ephemeral[0], ephemeral[1])
        self.table[x][y] = sign
        self.move_history[sign].append((x, y))
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
                *Scores(self.table, self.to_win, self.get_ephemeral()).get_move(
                    self.signs[self.turn_of]
                )
            )
        return True

    def _handle_ephemereness(self, x: int, y: int) -> None:
        self.table[x][y] = EMPTY

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

    def get_ephemeral(self) -> list[tuple[int, int]]:
        if self.ephemeral_threshold:
            return [
                history[0]
                for history in self.move_history.values()
                if len(history) == self.ephemeral_threshold
            ]
        return []

    def __str__(self):
        return (
            " vs ".join(self.gamers)
            + "\n"
            + self.prefix_str()
            + self._codeblock(self.table_str())
            + "\n"
            + self.signature_str()
        )

    @staticmethod
    def _codeblock(string: str) -> str:
        return f"```\n\u200b{string}```"

    def table_str(self) -> str:
        max_len = len(str(len(self.table)))
        text = " " * (max_len + 1) + " ".join(ascii_uppercase[: len(self.table)]) + "\n"
        ephemeral = self.get_ephemeral()
        for i, row in enumerate(self.table):
            text += (
                str(i + 1).rjust(max_len)
                + " "
                + " ".join(
                    x + EPHEMERENESS_SYMBOL if (i, j) in ephemeral else x
                    for j, x in enumerate(row)
                )
                + "\n"
            )
        return text

    def signature_str(self) -> str:
        if self.stopped:
            return t("tictac.stop.stopped", self.language)
        elif self.winner is None:
            return t(
                "tictac.current_player",
                self.language,
                player=self.gamers[self.turn_of],
                additional_info=self.additional_str(),
            )
        elif self.winner:
            return t("tictac.winner", self.language, winner=self.winner)
        else:
            return t("tictac.draw", self.language)

    def prefix_str(self) -> str:
        return ""

    def additional_str(self) -> str:
        return ""


class UltimateTicTacToe(TicTacToe):
    def __init__(self, *args, **kwargs):
        kwargs["use_ai"] = False
        super().__init__(*args, **kwargs)
        self._ttt_factory = lambda: TicTacToe(*args, **kwargs)
        self.subboards = [
            [self._ttt_factory() for _ in range(len(self.table))]
            for _ in range(len(self.table))
        ]
        self.selected_subboard_x = None
        self.selected_subboard_y = None

    def get_selected_subboard(self) -> TicTacToe | None:
        if self.selected_subboard_x is None:
            return None
        return self.subboards[self.selected_subboard_x][self.selected_subboard_y]

    def select_subboard(self, x: int | None, y: int | None) -> None:
        if x is None:
            empty_count = 0
            for i, row in enumerate(self.table):
                for j, cell in enumerate(row):
                    if cell == EMPTY:
                        empty_count += 1
                        empty_x = i
                        empty_y = j
            if empty_count == 1:
                x = empty_x
                y = empty_y
        self.selected_subboard_x = x
        self.selected_subboard_y = y

    def update(self, user_input: str) -> bool:
        subboard = self.get_selected_subboard()
        subboard_changed = False
        if not subboard:
            parts = user_input.split()
            if 1 <= len(parts) <= 2:
                coords = self._parse_cell(parts.pop(0))
                if coords is None:
                    return False
                self.select_subboard(coords[0], coords[1])
                subboard = self.get_selected_subboard()
                subboard_changed = True
                if subboard.winner is not None:
                    self.select_subboard(None, None)
                    return False
                if not parts:
                    return True
                user_input = parts[0]

        coords = self._parse_cell(user_input)
        if coords is None:
            return subboard_changed
        subboard.turn_of = self.turn_of
        x, y = coords
        if not subboard._update(x, y):
            return subboard_changed
        if not subboard.winner:
            self.turn_of = subboard.turn_of
            if subboard.winner is False:
                self.table[self.selected_subboard_x][self.selected_subboard_y] = " "
                if self.check_draw():
                    self.winner = False
                    return True
        else:
            self._update(self.selected_subboard_x, self.selected_subboard_y)
        self.select_subboard(x, y)
        if self.get_selected_subboard().winner is not None:
            self.select_subboard(None, None)
        return True

    def _handle_ephemereness(self, x: int, y: int) -> None:
        super()._handle_ephemereness(x, y)
        self.subboards[x][y] = self._ttt_factory()

    @staticmethod
    def _maybe_ephemeral(text: str, ephemeral: bool) -> str:
        if not ephemeral:
            return text
        return "".join(c if c.isspace() else c + EPHEMERENESS_SYMBOL for c in text)

    def table_str(self) -> str:
        ephemeral = self.get_ephemeral()
        rows = []
        max_number_length = len(str(len(self.subboards)))
        for i, subrow in enumerate(self.subboards):
            row_lines = []
            original_lines = [
                self._maybe_ephemeral(
                    board.table_str(), (i, j) in ephemeral
                ).splitlines()
                for j, board in enumerate(subrow)
            ]
            lines_length = len(original_lines[0])
            number = [" " * max_number_length] * lines_length
            number[(lines_length - 1) // 2] = str(i + 1).rjust(max_number_length)
            original_lines.insert(0, number)
            for lines in zip(*original_lines):
                row_lines.append(" | ".join(lines))
            rows.append("\n".join(row_lines))
        first_line = rows[0].split("\n", 1)[0]
        rows.insert(
            0,
            "|".join(
                f"{ascii_uppercase[i] if i >= 0 else ' ' :^{len(part)}}"
                for i, part in enumerate(first_line.split("|"), -1)
            ),
        )
        width = len(first_line)

        return f"\n{ '-' * width }\n".join(rows) + "\n"

    def prefix_str(self) -> str:
        return (
            t("tictac.main-board", self.language)
            + "\n"
            + self._codeblock(super().table_str())
            + "\n"
            + t("tictac.full-board", self.language)
            + "\n"
        )

    def additional_str(self) -> str:
        return (
            t(
                "tictac.selected_subboard",
                self.language,
                subboard=ascii_uppercase[self.selected_subboard_y]
                + str(self.selected_subboard_x + 1),
            )
            if self.selected_subboard_x is not None
            else t("tictac.subboard_not_selected", self.language)
        )
