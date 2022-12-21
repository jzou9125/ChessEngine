from dataclasses import dataclass, field
BOARD_LENGTH = 8


@dataclass
class BoardTile:
    row: int
    column: int
    _board_value: str = "--"
    color: str = "-"
    chess_piece: str = "-"

    def __str__(self):
        return self.board_value

    def capturable_by(self, color):
        return not self.is_empty and color != self.color

    @property
    def is_empty(self):
        return self.board_value == '--'

    @property
    def board_value(self):
        return self._board_value

    @board_value.setter
    def board_value(self, value):
        self._board_value = value
        self.color = value[0]
        self.chess_piece = value[1]





@dataclass
class Board:
    board: list[list[BoardTile]] = field(default_factory=list)


    def __post_init__(self):
        self.board = Board.generate_board()

    def get(self, row, column):
        return self.board[row][column]

    @staticmethod
    def generate_by_range(board, range, piece):
        for row, column in [(i, j) for i in (0, 7) for j in range]:
            board[row][column].board_value = ('w' if row == 7 else 'b') + piece

    @staticmethod
    def generate_board(BOARD_LENGTH=8):
        board = [[BoardTile(row, column) for column in range(BOARD_LENGTH)] for row in range(BOARD_LENGTH)]
        for column in range(BOARD_LENGTH):
            board[1][column].board_value = 'bp'
            board[6][column].board_value = 'wp'

        Board.generate_by_range(board, (0, 7), 'R')
        Board.generate_by_range(board, (1, 6), 'N')
        Board.generate_by_range(board, (2, 5), 'B')
        Board.generate_by_range(board, (3, 3), 'Q')
        Board.generate_by_range(board, (4, 4), 'K')
        return board
