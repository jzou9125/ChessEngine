from dataclasses import dataclass
from Board import BoardTile


@dataclass
class Move:
    starting_tile: BoardTile
    ending_tile: BoardTile
    piece_captured: str
    piece_moved: str
    ranksToRows = {'8': 0, '7': 1, '6': 2, '5': 3, '4': 4, '3': 5, '2': 6, '1': 7}
    rowsToRanks = {0: '8', 1: '7', 2: '6', 3: '5', 4: '4', 5: '3', 6: '2', 7: '1'}
    filesToColumns = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
    columnsToFiles = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'}

    def __post_init__(self):
        self.piece_captured = self.ending_tile.board_value
        self.piece_moved = self.starting_tile.board_value

    def process(self):
        self.ending_tile.board_value = self.piece_moved
        self.starting_tile.board_value = '--'

    def undo(self):
        self.starting_tile.board_value = self.piece_moved
        self.ending_tile.board_value = self.piece_captured

    @property
    def moved_king(self):
        return self.piece_moved[1] == 'K' or self.piece_captured[1] == 'K'

    @property
    def moved_pawn(self):
        return self.piece_moved[1] == 'p'

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

    def __str__(self):
        end_square = self.get_rank_file(self.end_row, self.end_column)
        if self.piece_moved[1] == 'p':
            if self.piece_captured != '--':
                return f"{self.columnsToFiles[self.start_column]}x{end_square}"
            else:
                return end_square
        return f"{self.piece_moved[1]}{'x' if self.piece_captured != '--' else ''}{end_square}"

    def get_rank_file(self, row, column):
        return self.columnsToFiles[column] + self.rowsToRanks[row]


@dataclass
class EnpassantMove(Move):
    enpassant_tile: BoardTile

    def __post_init__(self):
        self.piece_captured = self.enpassant_tile.board_value
        self.piece_moved = self.starting_tile.board_value

    def process(self):
        super().process()
        self.enpassant_tile.board_value = "--"

    def undo(self):
        super().undo()
        self.enpassant_tile.board_value = self.piece_captured

    def __str__(self):
        return f"{Move.columnsToFiles[self.start_row]}x{Move.columnsToFiles[self.end_row]}{self.end_column} e.p."


@dataclass
class CastleMove(Move):
    rook_original_tile: BoardTile
    rook_target_tile: BoardTile

    def __post_init__(self):
        self.piece_moved = self.starting_tile.board_value
        self.piece_captured = self.rook_original_tile.board_value

    def process(self):
        super().process()
        self.rook_target_tile.board_value = self.piece_captured
        self.rook_original_tile.board_value = '--'

    def undo(self):
        super().undo()
        self.rook_original_tile.board_value = self.piece_captured
        self.rook_target_tile.board_value = '--'

    def __str__(self):
        return '0-0' if self.rook_original_tile.column == 7 else '0-0-0'


@dataclass
class PromotionMove(Move):
    pass