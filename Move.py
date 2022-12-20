from dataclasses import dataclass

from Board import BoardTile, field

@dataclass
class Move:
    ranksToRows = {'8': 0, '7': 1, '6': 2, '5': 3, '4': 4, '3': 5, '2': 6, '1': 7}
    rowsToRanks = {0: '8', 1: '7', 2: '6', 3: '5', 4: '4', 5: '3', 6: '2', 7: '1'}
    filesToColumns = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
    columnsToFiles = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'}

    starting_tile: BoardTile
    ending_tile: BoardTile
    is_enpasant: bool = False
    is_castle: bool = False
    is_promotion: bool = False
    promotion_piece: str = ""
    piece_moved: str = ""
    piece_captured: str = ""
    special_tile: BoardTile = field(default_factory=BoardTile)

    def __post_init__(self):
        self.piece_captured = self.ending_tile.chess_piece
        self.piece_moved = self.starting_tile.chess_piece

    def process_move(self, move):
        self.board.get(move.start_row, move.start_column).board_value = '--'
        self.board.get(move.end_row,
                       move.end_column).board_value = move.promotionPiece if move.promotion else move.moved_piece
        if move.isEnPassant:
            self.board.get(move.start_row, move.end_column).board_value = '--'
        elif move.isCastle:
            rook_position = move.end_column + (-1 if move.end_column - move.start_column == 2 else 1)
            corner_position = move.end_column + (1 if move.end_column - move.start_column == 2 else -2)
            self.board.get(move.end_row, rook_position).board_value = self.board.get(move.end_row,
                                                                                     corner_position).board_value
            self.board.get(move.end_row, corner_position).board_value = '--'
        self.states.update_states(move)
    def process(self):
        self.ending_tile.chess_piece = self.promotion_piece if self.is_promotion else self.piece_moved
        self.starting_tile.chess_piece = '--'
        if self.is_enpasant:




    @property
    def end_row(self):
        return self.ending_tile.row
    @property
    def end_column(self):
        return self.ending_tile.column

    @property
    def end_square(self):
        return self.end_row, self.end_column

    @property
    def start_row(self):
        return self.starting_tile.row

    @property
    def start_column(self):
        return self.starting_tile.column

    @property
    def start_square(self):
        return self.start_row, self.start_column

    @property
    def captured(self):
        return self.piece_captured

    @property
    def moved_piece(self):
        return self.piece_moved

    def __str__(self):
        if self.is_castle:
            return '0-0' if self.end_column == 6 else '0-0-0'
        end_square = self.get_rank_file(self.end_row, self.end_column)
        if self.moved_piece[1] == 'p':
            if self.captured != '--':
                return f"{self.columnsToFiles[self.start_column]}x{end_square}"
            elif self.is_promotion:
                pass
            else:
                return end_square
        return f"{self.moved_piece[1]}{'x' if self.captured != '--' else ''}{end_square}"

    def get_rank_file(self, row, column):
        return self.columnsToFiles[column] + self.rowsToRanks[row]
