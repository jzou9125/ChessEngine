from dataclasses import dataclass, field, InitVar
from typing import Generator
from Board import Board


@dataclass
class Direction:
    row: int
    column: int
    direction: tuple
    board: InitVar[Board]
    board_size: int = field(init=False)
    generator_field: Generator = field(init=False)
    inside: bool = field(init=False)
    start_row: int = field(init=False)
    start_column: int = field(init=False)
    count: int = field(init=False)

    def __post_init__(self, board: Board):
        self.generator_field = self.travel_in_direction()
        self.start_row = self.row
        self.start_column = self.column
        self.row += self.direction[0]
        self.column += self.direction[1]
        self.board_size = board.board_size
        self.inside = self.inside_board()
        self.count = 1

    def travel_in_direction(self) -> Generator:
        """
            returns a direction object if the current coordinates are inside the board
        """
        while self.inside_board():
            yield self
            self.row += self.direction[0]
            self.column += self.direction[1]
            self.count += 1

    def inside_board(self) -> bool:
        """
            helper method to check if the row and column are inside the board
        """
        return self.row in range(self.board_size) and self.column in range(self.board_size)

    @property
    def single_pass(self) -> None:
        """
            used when we only require one iteration of travel in direction
        """
        for value in self.generator_field:
            yield value
            break


    @property
    def current_coords(self):
        return self.row, self.column

    @property
    def start_coords(self):
        return self.start_row, self.start_column

    @property
    def deltas(self):
        return self.direction, (-self.direction[0], - self.direction[1])
