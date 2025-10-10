from itertools import chain
from abc import ABC, abstractmethod
from typing import Iterable

TableT = list[list[str]]
EphemeralT = list[tuple[int, int]]
EMPTY = "_"


class MaxScoreBase(ABC):
    def __init__(
        self, table: TableT, to_win: int, x: int, y: int, ephemeral: EphemeralT
    ):
        self.table = table
        self.to_win = to_win
        self.score = 0
        self.start_x = self.end_x = x
        self.start_y = self.end_y = y
        self.symbol = EMPTY
        self.ephemeral = ephemeral
        self.has_space_before, self.has_space_after = False, False

    @abstractmethod
    def next(self, x: int, y: int) -> tuple[int, int]:
        raise NotImplementedError

    def move_start(self):
        self.start_x, self.start_y = self.next(self.start_x, self.start_y)

    def move_end(self):
        self.end_x, self.end_y = self.next(self.end_x, self.end_y)

    def iter_cells(self) -> Iterable[tuple[int, int]]:
        i, j = self.start_x, self.start_y
        while True:
            yield i, j
            if i == self.end_x and j == self.end_y:
                break
            i, j = self.next(i, j)

    def get_last_empty(self) -> tuple[int, int] | None:
        last = None
        for i, j in self.iter_cells():
            if self.table[i][j] == EMPTY:
                last = i, j
        return last

    def search(self):
        for _ in range(1, self.to_win):
            self.move_end()

        max_score = 0
        max_bounds = None
        max_symbol = EMPTY
        max_spaces = (False, False)
        has_space_before = False
        while (
            self.end_x < len(self.table)
            and self.end_y >= 0
            and self.end_y < len(self.table)
        ):
            i, j = self.next(self.end_x, self.end_y)
            has_space_after = (
                i < len(self.table)
                and j >= 0
                and j < len(self.table)
                and self.table[i][j] == EMPTY
            )
            symbol = EMPTY
            score = 0
            for i, j in self.iter_cells():
                if (i, j) in self.ephemeral:
                    continue
                cell = self.table[i][j]
                if cell != EMPTY:
                    if symbol == EMPTY:
                        symbol = cell
                        score = 1
                    elif symbol == cell:
                        score += 1
                    else:
                        score = 0
                        break

            if (
                score > max_score
                or score == max_score
                and has_space_before + has_space_after > sum(max_spaces)
            ):
                max_score = score
                max_bounds = (
                    (self.start_x, self.start_y),
                    (self.end_x, self.end_y),
                )
                max_symbol = symbol
                max_spaces = (
                    has_space_before
                    or has_space_after
                    and self.table[self.start_x][self.start_y] == EMPTY,
                    has_space_after,
                )
            has_space_before = self.table[self.start_x][self.start_y] == EMPTY
            self.move_start()
            self.move_end()
        if max_bounds is not None:
            self.score = max_score
            ((self.start_x, self.start_y), (self.end_x, self.end_y)) = max_bounds
            self.symbol = max_symbol
            self.has_space_before, self.has_space_after = max_spaces


class MaxScoreRow(MaxScoreBase):
    def next(self, x: int, y: int) -> tuple[int, int]:
        return x, y + 1


class MaxScoreCol(MaxScoreBase):
    def next(self, x: int, y: int) -> tuple[int, int]:
        return x + 1, y


class MaxScoreDiag1(MaxScoreBase):
    def next(self, x: int, y: int) -> tuple[int, int]:
        return x + 1, y + 1


class MaxScoreDiag2(MaxScoreBase):
    def next(self, x: int, y: int) -> tuple[int, int]:
        return x + 1, y - 1


class Scores:
    def __init__(self, table: TableT, to_win: int, ephemeral: EphemeralT = []):
        self.table = table
        self.to_win = to_win
        self.ephemeral = ephemeral
        self.search()

    def search(self):
        size = len(self.table)
        self.rows = [
            MaxScoreRow(self.table, self.to_win, x, 0, self.ephemeral)
            for x in range(size)
        ]
        self.cols = [
            MaxScoreCol(self.table, self.to_win, 0, y, self.ephemeral)
            for y in range(size)
        ]
        self.diags1 = [
            MaxScoreDiag1(self.table, self.to_win, 0, y, self.ephemeral)
            for y in range(size)
        ] + [
            MaxScoreDiag1(self.table, self.to_win, x, 0, self.ephemeral)
            for x in range(1, size)
        ]
        self.diags2 = [
            MaxScoreDiag2(self.table, self.to_win, 0, y, self.ephemeral)
            for y in range(size)
        ] + [
            MaxScoreDiag2(self.table, self.to_win, x, size - 1, self.ephemeral)
            for x in range(1, size)
        ]

        for s in self:
            s.search()

    def __iter__(self) -> Iterable[MaxScoreBase]:
        return chain(self.rows, self.cols, self.diags1, self.diags2)

    def get_move(self, bot_symbol: str) -> tuple[int, int]:
        target_score = self.to_win - 1
        for s in self:
            if s.symbol == bot_symbol and s.score == target_score:
                coords = s.get_last_empty()
                if coords:
                    return coords
        for s in self:
            if s.symbol != bot_symbol and (
                s.score == target_score
                or s.has_space_before
                and s.has_space_after
                and s.score == target_score - 1
            ):
                coords = s.get_last_empty()
                if coords:
                    return coords
        max_score = None
        for s in self:
            if s.symbol == bot_symbol:
                if max_score is None or s.score > max_score.score:
                    max_score = s
        if max_score is not None:
            coords = max_score.get_last_empty()
            if coords:
                return coords
        # this is not very smart...
        size = len(self.table) - 1
        for i, j in (
            (size // 2, size // 2),
            (0, 0),
            (0, size),
            (size, 0),
            (size, size),
        ):
            if self.table[i][j] == EMPTY:
                return i, j
        for i in range(size + 1):
            for j in range(size + 1):
                if self.table[i][j] == EMPTY:
                    return i, j
        raise RuntimeError("field is full")


if __name__ == "__main__":
    table = [
        ["x", "_", "_", "_", "_", "x", "_"],
        ["_", "_", "_", "_", "_", "_", "_"],
        ["_", "_", "_", "_", "_", "_", "_"],
        ["_", "_", "_", "_", "_", "_", "_"],
        ["_", "_", "_", "_", "_", "_", "_"],
        ["_", "_", "_", "_", "_", "_", "_"],
        ["_", "_", "_", "_", "_", "_", "_"],
    ]
    sc = Scores(table, 3)
    move = sc.get_move("o")
    print(move)
