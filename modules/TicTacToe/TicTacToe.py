from collections import defaultdict
from string import ascii_lowercase, ascii_uppercase

from modules.i18n import t
from .scores import EMPTY, Scores, MaxScoreBase

MAX_FIELD_SIZE = len(ascii_uppercase)
SIGNS = list(ascii_lowercase)
for redef_sign in reversed(("x", "o")):
    SIGNS.remove(redef_sign)
    SIGNS.insert(0, redef_sign)
del redef_sign
SIGNS = tuple(SIGNS)
MAX_PLAYERS = len(SIGNS)
EPHEMERENESS_SYMBOL = "\u036f"


class TicTacToe:
    def __init__(
        self,
        size: int,
        win_size: int,
        players: list[str],
        language="en",
        *,
        ai_players: list[str] = [],
        ephemeral_threshold=0,
    ):
        self.players = players
        self.ai_players = ai_players
        self.language = language
        self.signs = SIGNS[: len(players)]
        if len(self.signs) != len(self.players):
            raise ValueError("Too many players.")
        self.current_player_index = 0
        self.winner = None
        self.draw = False
        self.board = [[EMPTY] * size]
        for _ in range(1, size):
            self.board.append(self.board[0].copy())
        self.win_size = win_size
        self.move_history = defaultdict(list)
        self.ephemeral_threshold = ephemeral_threshold
        self.stopped = False

    def get_current_player(self) -> str:
        return self.players[self.current_player_index]

    def get_active_board(self) -> list[list[str]]:
        return self.board

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
        if letter >= len(self.board) or number not in range(len(self.board)):
            return None
        return number, letter

    def update(self, user_input: str) -> bool:
        coords = self._parse_cell(user_input)
        if coords is None:
            return False
        return self._update(coords[0], coords[1])

    def _update(self, x: int, y: int) -> bool:
        if self.board[x][y] != EMPTY:
            return False
        sign = self.signs[self.current_player_index]
        if (
            self.ephemeral_threshold
            and len(self.move_history[sign]) == self.ephemeral_threshold
        ):
            ephemeral = self.move_history[sign].pop(0)
            self._handle_ephemereness(ephemeral[0], ephemeral[1])
        self.board[x][y] = sign
        self.move_history[sign].append((x, y))

        self.current_player_index += 1
        if self.current_player_index == len(self.players):
            self.current_player_index = 0

        winning_score = self.get_winning_score()
        if winning_score:
            for i, j in winning_score.iter_cells():
                self.board[i][j] = self.board[i][j].upper()
            self.winner = next(
                player
                for player, sign in zip(self.players, self.signs)
                if sign == winning_score.symbol
            )
            return True
        if self.check_draw():
            self.draw = True
            return True

        if self.players[self.current_player_index] in self.ai_players:
            return self._update(
                *Scores(self.board, self.win_size, self.get_ephemeral()).get_move(
                    self.signs[self.current_player_index]
                )
            )
        return True

    def _handle_ephemereness(self, x: int, y: int) -> None:
        self.board[x][y] = EMPTY

    def check_draw(self) -> bool:
        for i in self.board:
            for j in i:
                if j == EMPTY:
                    return False
        return True

    def get_winning_score(self) -> MaxScoreBase | None:
        score = max(Scores(self.board, self.win_size), key=lambda x: x.score)
        if score.score >= self.win_size:
            return score
        return None

    def stop(self):
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
            " vs ".join(self.players)
            + "\n"
            + self.prefix_str()
            + self._codeblock(self.board_str())
            + "\n"
            + self.signature_str()
        )

    @staticmethod
    def _codeblock(string: str) -> str:
        return f"```\n\u200b{string}```"

    def board_str(self) -> str:
        max_len = len(str(len(self.board)))
        text = " " * (max_len + 1) + " ".join(ascii_uppercase[: len(self.board)]) + "\n"
        ephemeral = self.get_ephemeral()
        for i, row in enumerate(self.board):
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
        if self.draw:
            return t("tictac.draw", self.language)
        elif self.winner is None:
            if self.stopped:
                return t("tictac.stop.stopped", self.language)
            return t(
                "tictac.current_player",
                self.language,
                player=self.players[self.current_player_index],
                additional_info=self.suffix_str(),
            )
        else:
            return t("tictac.winner", self.language, winner=self.winner)

    def prefix_str(self) -> str:
        return ""

    def suffix_str(self) -> str:
        return ""


class UltimateTicTacToe(TicTacToe):
    def __init__(self, *args, **kwargs):
        kwargs["ai_players"] = []
        super().__init__(*args, **kwargs)
        self._ttt_factory = lambda: TicTacToe(*args, **kwargs)
        self.subboards = [
            [self._ttt_factory() for _ in range(len(self.board))]
            for _ in range(len(self.board))
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
            for i, row in enumerate(self.board):
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

    def get_active_board(self) -> list[list[str]]:
        subboard = self.get_selected_subboard()
        if not subboard:
            return super().get_active_board()
        return subboard.get_active_board()

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
                if subboard.winner is not None or subboard.draw:
                    self.select_subboard(None, None)
                    return False
                if not parts:
                    return True
                user_input = parts[0]

        coords = self._parse_cell(user_input)
        if coords is None:
            return subboard_changed
        subboard.current_player_index = self.current_player_index
        x, y = coords
        if not subboard._update(x, y):
            return subboard_changed

        if subboard.draw:
            self.current_player_index = subboard.current_player_index
            self.board[self.selected_subboard_x][self.selected_subboard_y] = " "
            if self.check_draw():
                self.draw = True
                return True
        elif subboard.winner is None:
            self.current_player_index = subboard.current_player_index
        else:
            self._update(self.selected_subboard_x, self.selected_subboard_y)
        self.select_subboard(x, y)
        subboard = self.get_selected_subboard()
        if subboard.winner is not None or subboard.draw:
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

    def board_str(self) -> str:
        ephemeral = self.get_ephemeral()
        rows = []
        max_number_length = len(str(len(self.subboards)))
        for i, subrow in enumerate(self.subboards):
            row_lines = []
            original_lines = [
                self._maybe_ephemeral(
                    board.board_str(), (i, j) in ephemeral
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
            + self._codeblock(super().board_str())
            + "\n"
            + t("tictac.full-board", self.language)
            + "\n"
        )

    def suffix_str(self) -> str:
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
