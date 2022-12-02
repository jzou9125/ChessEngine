# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

class GameState:
    def __init__(self):
        self.board = [
            ['bR', 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR'],
            ['bp', 'bp', 'bp', 'bp', 'bp', 'bp', 'bp', 'bp'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['wp', 'wp', 'wp', 'wp', 'wp', 'wp', 'wp', 'wp'],
            ['wR', 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR'],
        ]
        self.moveFunctions = {'p': self.get_pawn_moves, 'R': self.get_rook_moves, 'N': self.get_knight_moves,
                              'B': self.get_bishop_moves, 'Q': self.get_queen_moves, 'K': self.get_king_moves}
        self.BOARDLENGTH = len(self.board)
        self.whiteToMove = True
        self.moveLog = []
        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)
        self.checkmate = False
        self.stalemate = False

    def process_move(self, move):
        if move.pieceMoved == 'wK':
            self.white_king_location = move.endRow, move.endColumn
        elif move.pieceMoved == 'bK':
            self.black_king_location = move.endRow, move.endColumn

        self.board[move.startRow][move.startColumn] = '--'
        self.board[move.endRow][move.endColumn] = move.pieceMoved
        self.moveLog.append(move)
        self.change_turn()

    def undo_move(self):
        if not self.moveLog:
            return None
        last_move = self.moveLog.pop()
        self.board[last_move.endRow][last_move.endColumn] = last_move.pieceCaptured
        self.board[last_move.startRow][last_move.startColumn] = last_move.pieceMoved

        if last_move.pieceMoved == 'wK':
            self.white_king_location = last_move.startRow, last_move.startColumn
        if last_move.pieceMoved == 'bK':
            self.black_king_location = last_move.startRow, last_move.startColumn

        self.change_turn()


    def change_turn(self):
        self.whiteToMove = not self.whiteToMove

    def get_valid_moves(self):
        possible_moves = self.get_all_possible_moves()
        for i in range(len(possible_moves)-1, -1, -1):
            self.process_move(possible_moves[i])
            self.change_turn()
            if self.is_checked():
                possible_moves.remove(possible_moves[i])
            self.change_turn()
            self.undo_move()

        if len(possible_moves) == 0:
            self.checkmate = self.is_checked()
            self.stalemate = not self.checkmate
        else:
            self.checkmate = False
            self.stalemate = False

        return possible_moves

    def is_checked(self):
        if self.whiteToMove:
            return self.square_undered_attack(*self.white_king_location)
        else:
            return self.square_undered_attack(*self.black_king_location)

    def square_undered_attack(self, row, column):
        self.change_turn()
        oppponent_moves = self.get_all_possible_moves()
        self.change_turn()
        for move in oppponent_moves:
            if move.endRow  == row and move.endColumn == column:
                return True
        return False

    def get_all_possible_moves(self):
        moves = []
        for row in range(self.BOARDLENGTH):
            for column in range(self.BOARDLENGTH):
                color = self.board[row][column][0]
                if color == 'w' and self.whiteToMove or (color == 'b' and not self.whiteToMove):
                    piece = self.board[row][column][1]
                    self.moveFunctions[piece](row, column, moves)

        return moves

    def get_pawn_moves(self, row, column, moves):
        direction = -1 if self.whiteToMove else 1
        capture = 'b' if self.whiteToMove else 'w'
        double_jump = 6 if self.whiteToMove else 1

        if self.board[row + direction][column] == '--':
            moves.append(Move((row, column), (row + direction, column), self.board))
            if row == double_jump and self.board[row + direction * 2][column] == '--':
                moves.append(Move((row, column), (row + direction * 2, column), self.board))
        if column - 1 >= 0:
            if self.board[row + direction][column - 1][0] == capture:
                moves.append(Move((row, column), (row + direction, column - 1), self.board))
        if column + 1 < self.BOARDLENGTH:
            if self.board[row + direction][column + 1][0] == capture:
                moves.append(Move((row, column), (row + direction, column + 1), self.board))

    def get_rook_moves(self, row, column, moves):
        capture = 'b' if self.whiteToMove else 'w'
        directions = ((1, 0), (0, 1), (-1, 0), (0, -1))
        for changeRow, changeColumn in directions:
            for i in range(1, self.BOARDLENGTH):
                end_row, end_column = row + changeRow * i, column + changeColumn * i
                if self.inside_board(end_row, end_column):
                    end_piece = self.board[end_row][end_column]
                    if end_piece == '--':
                        moves.append(Move((row, column), (end_row, end_column), self.board))
                    elif end_piece[0] == capture:
                        moves.append(Move((row, column), (end_row, end_column), self.board))
                        break
                    else:
                        break
                else:
                    break

    def get_knight_moves(self, row, column, moves):
        capture = 'b' if self.whiteToMove else 'w'
        directions = ((1, 2), (1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1), (-1, 2), (-1, -2))
        for changeRow, changeColumn in directions:
            end_row, end_column = row + changeRow, column + changeColumn
            if self.inside_board(end_row, end_column):
                if self.board[end_row][end_column] == '--' or self.board[end_row][end_column][0] == capture:
                    moves.append(Move((row, column), (end_row, end_column), self.board))

    def get_bishop_moves(self, row, column, moves):
        capture = 'b' if self.whiteToMove else 'w'
        directions = ((1, 1), (-1, -1), (1, -1), (-1, 1))
        for changeRow, changeColumn in directions:
            for i in range(1, self.BOARDLENGTH):
                end_row, end_column = row + changeRow * i, column + changeColumn * i
                if self.inside_board(end_row, end_column):
                    if self.board[end_row][end_column] == '--':
                        moves.append(Move((row, column), (end_row, end_column), self.board))
                    elif self.board[end_row][end_column][0] == capture:
                        moves.append(Move((row, column), (end_row, end_column), self.board))
                        break
                    else:
                        break
                else:
                    break

    def get_queen_moves(self, row, column, moves):
        capture = 'b' if self.whiteToMove else 'w'
        directions = ((1, 1), (-1, -1), (1, -1), (-1, 1), (1, 0), (-1, 0), (0, -1), (0, 1))
        for changeRow, changeColumn in directions:
            for i in range(1, self.BOARDLENGTH):
                end_row, end_column = row + changeRow * i, column + changeColumn * i
                if self.inside_board(end_row, end_column):
                    if self.board[end_row][end_column] == '--':
                        moves.append(Move((row, column), (end_row, end_column), self.board))
                    elif self.board[end_row][end_column][0] == capture:
                        moves.append(Move((row, column), (end_row, end_column), self.board))
                        break
                    else:
                        break
                else:
                    break

    def get_king_moves(self, row, column, moves):
        capture = 'b' if self.whiteToMove else 'w'
        directions = ((1, 1), (-1, -1), (1, -1), (-1, 1), (1, 0), (-1, 0), (0, -1), (0, 1))
        for changeRow, changeColumn in directions:
            end_row, end_column = row + changeRow, column + changeColumn
            if self.inside_board(end_row, end_column):
                if self.board[end_row][end_column] == '--':
                    moves.append(Move((row, column), (end_row, end_column), self.board))
                elif self.board[end_row][end_column][0] == capture:
                    moves.append(Move((row, column), (end_row, end_column), self.board))
        # didn't include castle yet

    def inside_board(self, row, column):
        return row in range(self.BOARDLENGTH) and column in range(self.BOARDLENGTH)


class Move:
    ranksToRows = {'8': 0, '7': 1, '6': 2, '5': 3, '4': 4, '3': 5, '2': 6, '1': 7}
    rowsToRanks = {0: '8', 1: '7', 2: '6', 3: '5', 4: '4', 5: '3', 6: '2', 7: '1'}
    filesToColumns = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
    columnsToFiles = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'}

    def __init__(self, starting_square, target_square, board):
        self.startRow, self.startColumn = starting_square
        self.endRow, self.endColumn = target_square
        self.pieceMoved = board[self.startRow][self.startColumn]
        self.pieceCaptured = board[self.endRow][self.endColumn]
        self.moveId = self.startRow * 1000 + self.startColumn * 100 + self.endRow * 10 + self.endColumn

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveId == other.moveId
        return False

    def get_chess_notation(self):
        return self.get_rank_file(self.startRow, self.startColumn) + self.get_rank_file(self.endRow, self.endColumn)

    def get_rank_file(self, row, column):
        return self.columnsToFiles[column] + self.rowsToRanks[row]
