

class Move:
    ranksToRows = {'8': 0, '7': 1, '6': 2, '5': 3, '4': 4, '3': 5, '2': 6, '1': 7}
    rowsToRanks = {0: '8', 1: '7', 2: '6', 3: '5', 4: '4', 5: '3', 6: '2', 7: '1'}
    filesToColumns = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
    columnsToFiles = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'}

    def __init__(self, starting_square, target_square, board, is_enpassant=False, is_castle=False):
        self._start_row, self._start_column = starting_square
        self._end_row, self._end_column = target_square
        self.piece_moved = board[self._start_row][self._start_column]
        self.piece_captured = board[self.end_row][self.end_column]
        self.is_promotion = (self.moved_piece == 'wp' and self.end_row == 0) or \
                            (self.moved_piece == 'bp' and self.end_row == 7)
        self.promotionPiece = None
        self.isEnPassant = is_enpassant
        self.isCastle = is_castle

    @property
    def end_square(self):
        return self.end_row, self.end_column

    @property
    def end_row(self):
        return self._end_row

    @property
    def end_column(self):
        return self._end_column

    @property
    def start_square(self):
        return self.start_row, self.start_column

    @property
    def start_row(self):
        return self._start_row

    @property
    def start_column(self):
        return self._start_column

    @property
    def captured(self):
        return self.piece_captured

    @property
    def moved_piece(self):
        return self.piece_moved

    @property
    def promotion(self):
        return self.is_promotion

    def __str__(self):
        if self.isCastle:
            return '0-0' if self.end_column == 6 else '0-0-0'
        end_square = self.get_rank_file(self.end_row, self.end_column)
        if self.moved_piece[1] == 'p':
            if self.captured != '--':
                return f"{self.columnsToFiles[self.start_column]}x{end_square}"
            elif self.promotion:
                pass
            else:
                return end_square
        return f"{self.moved_piece[1]}{'x' if self.captured != '--' else ''}{end_square}"

    def get_rank_file(self, row, column):
        return self.columnsToFiles[column] + self.rowsToRanks[row]
