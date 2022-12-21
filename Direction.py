from dataclasses import dataclass
from typing import Generator

BOARDLENGTH = 8


def inside_board(row, column):
    return row in range(BOARDLENGTH) and column in range(BOARDLENGTH)


@dataclass
class Direction:
    row: int
    column: int
    direction: tuple
    count: int = 1
    generator_field: Generator = None
    inside: bool = True
    start_row: int = None
    start_column: int = None

    def __post_init__(self):
        self.generator_field = self.travel_in_direction()
        self.start_row = self.row
        self.start_column = self.column
        self.row += self.direction[0]
        self.column += self.direction[1]
        self.inside = inside_board(self.row, self.column)

    def travel_in_direction(self):
        while inside_board(self.row, self.column):
            yield self
            self.row += self.direction[0]
            self.column += self.direction[1]
            self.count += 1

    @property
    def single_pass(self):
        for value in self.generator_field:
            yield value
            break

    @property
    def full_coords(self):
        return self.start_row, self.start_column, self.row, self.column

    @property
    def current_coords(self):
        return self.row, self.column

    @property
    def start_coords(self):
        return self.start_row, self.start_column

    @property
    def delta_row(self):
        return self.direction[0]

    @property
    def delta_column(self):
        return self.direction[1]

    @property
    def deltas(self):
        return self.direction, (-self.delta_row, - self.delta_column)
