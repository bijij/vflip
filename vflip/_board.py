"""
MIT License

Copyright (c) 2021-present Josh B

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

import random
from typing import TypeVar, Union, overload

from PIL import Image

from .types import *
from .utils import BASE_DIR

__all__ = ("Board", "Square")


_ST = TypeVar("_ST", bound="Square")


VALUES: list[Value] = [0, 1, 2, 3]


# PIL templates

VALUES_SHEET = Image.open(BASE_DIR / "res/values.png")
NUMBERS_SHEET = Image.open(BASE_DIR / "res/numbers.png")
NOTES_SHEET = Image.open(BASE_DIR / "res/notes.png")


SQUARE_TEMPLATE = Image.open(BASE_DIR / "res/square.png")
SQUARE_TEMPLATE_FLIPPED = Image.open(BASE_DIR / "res/square_flipped.png")
BOARD_TEMPLATE = Image.open(BASE_DIR / "res/board.png")

SQUARE_SIZE = SQUARE_TEMPLATE.width
VALUE_SIZE = VALUES_SHEET.height
NOTE_SIZE = NOTES_SHEET.height

NUMBER_WIDTH = NUMBERS_SHEET.width // 10
NUMBER_HEIGHT = NUMBERS_SHEET.height

SQUARE_VALUES: dict[Value, Image.Image] = {
    value: VALUES_SHEET.crop((VALUE_SIZE * value, 0, VALUE_SIZE * (value + 1), VALUE_SIZE)) for value in VALUES
}

NUMBERS: list[Image.Image] = [
    NUMBERS_SHEET.crop((NUMBER_WIDTH * n, 0, NUMBER_WIDTH * (n + 1), NUMBER_HEIGHT)) for n in range(10)
]

NOTES: dict[Value, Image.Image] = {
    value: NOTES_SHEET.crop((NOTE_SIZE * value, 0, NOTE_SIZE * (value + 1), NOTE_SIZE)) for value in VALUES
}

NOTE_OFFSETS: dict[Value, tuple[int, int]] = {
    0: (1, 1),
    1: (SQUARE_SIZE - NOTE_SIZE, 1),
    2: (1, SQUARE_SIZE - NOTE_SIZE),
    3: (SQUARE_SIZE - NOTE_SIZE, SQUARE_SIZE - NOTE_SIZE),
}

LINE_TEMPLATE = Image.new("RGBA", (SQUARE_SIZE + 2, SQUARE_SIZE + 2), (0, 0, 0, 0))

LINE_POINTS_OFFSET = (9, 0)
LINE_VOLTORB_OFFSET = (17, 13)

SQUARE_OFFSET = 3
SQUARE_MARGIN = 10

VALUE_OFFSET = (SQUARE_SIZE - VALUE_SIZE) // 2


CONFIGURATIONS: dict[Level, list[Configuration]] = {
    1: [
        (3, 1, 6),
        (0, 3, 6),
        (5, 0, 6),
        (2, 2, 6),
        (4, 1, 6),
    ],
    2: [
        (1, 3, 7),
        (6, 0, 7),
        (3, 2, 7),
        (0, 4, 7),
        (5, 1, 7),
    ],
    3: [
        (2, 3, 8),
        (7, 0, 8),
        (4, 2, 8),
        (1, 4, 8),
        (6, 1, 8),
    ],
    4: [
        (3, 3, 8),
        (0, 5, 8),
        (8, 0, 10),
        (5, 2, 10),
        (2, 4, 10),
    ],
    5: [
        (7, 1, 10),
        (4, 3, 10),
        (1, 5, 10),
        (9, 9, 10),
        (6, 2, 10),
    ],
    6: [
        (3, 4, 10),
        (0, 6, 10),
        (8, 1, 10),
        (5, 3, 10),
        (2, 5, 10),
    ],
    7: [
        (7, 2, 10),
        (4, 4, 10),
        (1, 6, 13),
        (9, 1, 13),
        (6, 3, 10),
    ],
    8: [
        (0, 7, 10),
        (8, 2, 10),
        (5, 4, 10),
        (2, 6, 10),
        (7, 3, 10),
    ],
}


class Square:
    def __init__(self, value: Value) -> None:
        self.value: Value = value
        self.flipped = False
        self.notes: dict[Value, bool] = {value: False for value in VALUES}

    def note(self, value: Value) -> None:
        if self.flipped:
            raise RuntimeError("Cannot note a flipped square.")
        self.notes[value] = not self.notes[value]

    def flip(self) -> None:
        if self.flipped:
            raise RuntimeError("This square has already been flipped.")
        self.flipped = True

    def _render(self) -> Image.Image:
        if self.flipped:
            return self._render_flipped()

        image = SQUARE_TEMPLATE.copy()

        for value, marked in self.notes.items():
            if marked:
                image.paste(NOTES[value], NOTE_OFFSETS[value], NOTES[value])

        return image

    def _render_flipped(self) -> Image.Image:
        image = SQUARE_TEMPLATE_FLIPPED.copy()

        value = SQUARE_VALUES[self.value]

        x = y = VALUE_OFFSET
        image.paste(value, (x, y), value)

        return image

    def __repr__(self) -> str:
        return "<Square value={0.value} >".format(self)

    @classmethod
    def random(cls: type[_ST]) -> _ST:
        return cls(random.choice(VALUES))


class Line:
    def __init__(self, squares: list[Square]) -> None:
        self.squares = squares

    @property
    def points(self) -> int:
        return sum(square.value for square in self.squares)

    @property
    def voltorbs(self) -> int:
        return sum(square.value == 0 for square in self.squares)

    def _render(self) -> Image.Image:
        image = LINE_TEMPLATE.copy()

        x, y = LINE_POINTS_OFFSET
        for n in (int(n) for n in f"{self.points:02}"):
            image.paste(NUMBERS[n], (x, y), NUMBERS[n])
            x += NUMBER_WIDTH + 2

        image.paste(NUMBERS[self.voltorbs], LINE_VOLTORB_OFFSET, NUMBERS[self.voltorbs])

        return image


class Board:
    def __init__(self, level: Level) -> None:
        n_2, n_3, n_0 = random.choice(CONFIGURATIONS[level])
        n_1 = 25 - (n_2 + n_3 + n_0)

        values = []
        for value, n in enumerate((n_0, n_1, n_2, n_3)):
            values.extend(Square(value) for _ in range(n))  # type: ignore
        random.shuffle(values)

        self.grid: list[list[Square]] = [[values[row * 5 + col] for col in range(5)] for row in range(5)]
        self.level: Level = level

    @overload
    def __getitem__(self, index=tuple[Index, Index]) -> Square:
        ...

    @overload
    def __getitem__(self, index=tuple[slice, Index]) -> list[Square]:
        ...

    @overload
    def __getitem__(self, index=tuple[Index, slice]) -> list[Square]:
        ...

    @overload
    def __getitem__(self, index=tuple[slice, slice]) -> list[list[Square]]:
        ...

    def __getitem__(
        self, index=tuple[Union[Index, slice], Union[Index, slice]]
    ) -> Union[Square, list[Square], list[list[Square]]]:
        row, col = index
        return self.grid[row][col]

    @property
    def rows(self) -> list[Line]:
        lines = []
        for row in range(5):
            lines.append(Line(self.grid[row]))
        return lines

    @property
    def cols(self) -> list[Line]:
        lines = []
        for col in range(5):
            lines.append(Line([self.grid[row][col] for row in range(5)]))
        return lines

    @property
    def squares(self) -> list[Square]:
        squares = []
        for row in self.rows:
            squares.extend(row.squares)
        return squares

    @property
    def points(self) -> int:
        total = 1
        for square in self.squares:
            if square.flipped:
                total *= square.value
        return total

    @property
    def over(self) -> bool:
        # Check for revealed 0
        for square in self.squares:
            if square.flipped and square.value == 0:
                return True

        # Check for hidden 2/3
        for square in self.squares:
            if square.value in (2, 3) and not square.flipped:
                return False

        return True

    def flip(self, row: Index, col: Index) -> None:
        return self[row, col].flip()

    def note(self, row: Index, col: Index, value: Value) -> None:
        return self[row, col].note(value)

    def _render(self) -> Image.Image:

        image = BOARD_TEMPLATE.copy()

        # Populate squares
        y = SQUARE_OFFSET
        for row in self.rows:
            x = SQUARE_OFFSET
            for col in range(5):
                square = row.squares[col]._render()
                image.paste(square, (x, y))
                x += SQUARE_SIZE + SQUARE_MARGIN
            line = row._render()
            image.paste(line, (x - 1, y - 1), line)
            y += SQUARE_SIZE + SQUARE_MARGIN

        x = SQUARE_OFFSET
        for col in self.cols:
            line = col._render()
            image.paste(line, (x - 1, y - 1), line)
            x += SQUARE_SIZE + SQUARE_MARGIN

        return image
