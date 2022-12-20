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
    def generate_nrb(board, range, piece):
        for row, column in [(i, j) for i in (0, 7) for j in range]:
            board[row][column].board_value = ('w' if row == 7 else 'b') + piece

    @staticmethod
    def generate_board(BOARDLENGTH=8):
        board = [[BoardTile(row, column) for column in range(BOARDLENGTH)] for row in range(BOARDLENGTH)]
        for column in range(BOARDLENGTH):
            board[1][column].board_value = 'bp'
            board[6][column].board_value = 'wp'

        Board.generate_nrb(board, (0, 7), 'R')
        Board.generate_nrb(board, (1, 6), 'N')
        Board.generate_nrb(board, (2, 5), 'B')
        Board.generate_nrb(board, (3, 3), 'Q')
        Board.generate_nrb(board, (4, 4), 'K')
        return board
