# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import copy

class GameState:
    def __init__(self):
        self.staleMate = False
        self.checkMate = False
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
        self.inChecked = False
        self.pins = []
        self.checks = []
        self.enpassantPossible = ()
        self.enpassantLog = [self.enpassantPossible]
        self.castleRights = CastleRight(True, True, True, True)
        self.castleRightLogs = [
            CastleRight(self.castleRights.wks, self.castleRights.bks, self.castleRights.wqs, self.castleRights.bqs)]

    def process_move(self, move):
        if move.pieceMoved == 'wK':
            self.white_king_location = move.endRow, move.endColumn
        elif move.pieceMoved == 'bK':
            self.black_king_location = move.endRow, move.endColumn

        self.board[move.startRow][move.startColumn] = '--'
        self.board[move.endRow][move.endColumn] = move.promotionPiece if move.isPromotion else move.pieceMoved
        if move.pieceMoved[1] == 'p' and abs(move.startRow - move.endRow) == 2:
            self.enpassantPossible = ((move.startRow + move.endRow) // 2, move.startColumn)
        else:
            self.enpassantPossible = ()

        if move.isEnPassant:
            self.board[move.startRow][move.endColumn] = '--'

        if move.isCastle:
            if move.endColumn - move.startColumn == 2:
                self.board[move.endRow][move.endColumn - 1] = self.board[move.endRow][move.endColumn + 1]
                self.board[move.endRow][move.endColumn + 1] = '--'
            else:
                self.board[move.endRow][move.endColumn + 1] = self.board[move.endRow][move.endColumn - 2]
                self.board[move.endRow][move.endColumn - 2] = '--'

        self.update_castle_rights(move)
        self.castleRightLogs.append(
            CastleRight(self.castleRights.wks, self.castleRights.bks, self.castleRights.wqs, self.castleRights.bqs))
        self.moveLog.append(move)
        self.enpassantLog.append(self.enpassantPossible)
        self.change_turn()

    def undo_move(self):
        if not self.moveLog:
            return None

        last_move = self.moveLog.pop()
        self.board[last_move.endRow][last_move.endColumn] = last_move.pieceCaptured
        self.board[last_move.startRow][last_move.startColumn] = last_move.pieceMoved

        if last_move.isEnPassant:
            self.board[last_move.startRow][last_move.endColumn] = ('w' if last_move.pieceMoved[0] == 'b' else 'b') + 'p'

        if last_move.pieceMoved == 'wK':
            self.white_king_location = last_move.startRow, last_move.startColumn
        if last_move.pieceMoved == 'bK':
            self.black_king_location = last_move.startRow, last_move.startColumn

        self.enpassantLog.pop()
        self.enpassantPossible = self.enpassantLog[-1]
        self.castleRightLogs.pop()
        self.castleRights = copy.deepcopy(self.castleRightLogs[-1])
        if last_move.isCastle:
            if last_move.endColumn - last_move.startColumn == 2:
                self.board[last_move.endRow][last_move.endColumn + 1] = self.board[last_move.endRow][
                    last_move.endColumn - 1]
                self.board[last_move.endRow][last_move.endColumn - 1] = '--'
            else:
                self.board[last_move.endRow][last_move.endColumn - 2] = self.board[last_move.endRow][
                    last_move.endColumn + 1]
                self.board[last_move.endRow][last_move.endColumn + 1] = '--'
        self.change_turn()
        self.checkMate = False
        self.staleMate = False

    def change_turn(self):
        self.whiteToMove = not self.whiteToMove

    def get_valid_moves(self):
        possible_moves = []
        # possible_moves = self.get_all_possible_moves()
        self.inChecked, self.pins, self.checks = self.check_for_pins_and_checks()
        king_row, king_column = self.white_king_location if self.whiteToMove else self.black_king_location
        if self.inChecked:
            if len(self.checks) == 1:
                possible_moves = self.get_all_possible_moves()
                check = self.checks[0]
                check_row, check_column = check[0], check[1]
                piece_checking = self.board[check_row][check_column]
                valid_squares = []
                if piece_checking[1] == 'N':
                    valid_squares = [(check_row, check_column)]
                else:
                    for i in range(1, self.BOARDLENGTH):
                        valid_square = (king_row + check[2] * i, king_column + check[3] * i)
                        valid_squares.append(valid_square)
                        if valid_square[0] == check_row and valid_square[1] == check_column:
                            break
                for i in range(len(possible_moves) - 1, -1, -1):
                    if possible_moves[i].pieceMoved[1] != 'K':
                        if not (possible_moves[i].endRow, possible_moves[i].endColumn) in valid_squares:
                            possible_moves.remove(possible_moves[i])
            else:
                self.get_king_moves(king_row, king_column, possible_moves)
        else:
            possible_moves = self.get_all_possible_moves()
            self.get_castle_moves(king_row, king_column, possible_moves)

        if len(possible_moves) == 0:
            if self.inChecked:
                self.checkMate = True
            else:
                self.staleMate = True

        return possible_moves

    def is_pinned(self, row, column):
        pinned, pin_direction = False, ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == column:
                pinned = True
                pin_direction = self.pins[i][2], self.pins[i][3]
                self.pins.remove(self.pins[i])
        return pinned, pin_direction

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
        piece_pinned, pin_direction = self.is_pinned(row, column)
        direction = -1 if self.whiteToMove else 1
        capture = 'b' if self.whiteToMove else 'w'
        double_jump = 6 if self.whiteToMove else 1

        if self.board[row + direction][column] == '--':
            if not piece_pinned or pin_direction == (direction, 0):
                moves.append(Move((row, column), (row + direction, column), self.board))
                if row == double_jump and self.board[row + direction * 2][column] == '--':
                    moves.append(Move((row, column), (row + direction * 2, column), self.board))
        if column - 1 >= 0:
            if not piece_pinned or pin_direction == (direction, -1):
                if self.board[row + direction][column - 1][0] == capture:
                    moves.append(Move((row, column), (row + direction, column - 1), self.board))
                elif (row + direction, column - 1) == self.enpassantPossible:
                    moves.append(Move((row, column), (row + direction, column - 1), self.board, is_enpassant=True))
        if column + 1 < self.BOARDLENGTH:
            if not piece_pinned or pin_direction == (direction, 1):
                if self.board[row + direction][column + 1][0] == capture:
                    moves.append(Move((row, column), (row + direction, column + 1), self.board))
                elif (row + direction, column + 1) == self.enpassantPossible:
                    moves.append(Move((row, column), (row + direction, column + 1), self.board, is_enpassant=True))

    def get_rook_moves(self, row, column, moves):
        piece_pinned, pin_direction = self.is_pinned(row, column)
        capture = 'b' if self.whiteToMove else 'w'
        directions = ((1, 0), (0, 1), (-1, 0), (0, -1))
        for change_row, change_column in directions:
            if not piece_pinned or pin_direction == (change_row, change_column) or \
                    pin_direction == (-change_row, -change_column):
                for i in range(1, self.BOARDLENGTH):
                    end_row, end_column = row + change_row * i, column + change_column * i
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
        piece_pinned, pin_direction = self.is_pinned(row, column)
        if piece_pinned:
            return
        capture = 'b' if self.whiteToMove else 'w'
        directions = ((1, 2), (1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1), (-1, 2), (-1, -2))
        for change_row, change_column in directions:
            end_row, end_column = row + change_row, column + change_column
            if self.inside_board(end_row, end_column):
                if self.board[end_row][end_column] == '--' or self.board[end_row][end_column][0] == capture:
                    moves.append(Move((row, column), (end_row, end_column), self.board))

    def get_bishop_moves(self, row, column, moves):
        piece_pinned, pin_direction = self.is_pinned(row, column)
        capture = 'b' if self.whiteToMove else 'w'
        directions = ((1, 1), (-1, -1), (1, -1), (-1, 1))
        for change_row, change_column in directions:
            if not piece_pinned or pin_direction == (change_row, change_column) \
                    or pin_direction == (-change_row, -change_column):
                for i in range(1, self.BOARDLENGTH):
                    end_row, end_column = row + change_row * i, column + change_column * i
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
        piece_pinned, pin_direction = self.is_pinned(row, column)
        capture = 'b' if self.whiteToMove else 'w'
        directions = ((1, 1), (-1, -1), (1, -1), (-1, 1), (1, 0), (-1, 0), (0, -1), (0, 1))
        for change_row, change_column in directions:
            if not piece_pinned or pin_direction == (change_row, change_column) or \
                    pin_direction == (-change_row, -change_column):
                for i in range(1, self.BOARDLENGTH):
                    end_row, end_column = row + change_row * i, column + change_column * i
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
        directions = ((1, 1), (-1, -1), (1, -1), (-1, 1), (1, 0), (-1, 0), (0, -1), (0, 1))
        for changeRow, changeColumn in directions:
            end_row, end_column = row + changeRow, column + changeColumn
            if self.inside_board(end_row, end_column):
                end_piece = self.board[end_row][end_column]
                if end_piece[0] != ('w' if self.whiteToMove else 'b'):
                    if self.whiteToMove:
                        self.white_king_location = (end_row, end_column)
                    else:
                        self.black_king_location = end_row, end_column
                    in_check, pins, checks = self.check_for_pins_and_checks()
                    if not in_check:
                        moves.append(Move((row, column), (end_row, end_column), self.board))
                    # elif len(checks) == 1:
                        #there is a bug that stops the king from taking the piece that is checking it
                    if self.whiteToMove:
                        self.white_king_location = (row, column)
                    else:
                        self.black_king_location = row, column

    def inside_board(self, row, column):
        return row in range(self.BOARDLENGTH) and column in range(self.BOARDLENGTH)

    def check_for_pins_and_checks(self):
        pins, checks, in_check = [], [], False
        enemy = 'b' if self.whiteToMove else 'w'
        ally = 'w' if self.whiteToMove else 'b'
        start_row, start_col = self.white_king_location if self.whiteToMove else self.black_king_location
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            change_row, change_column = directions[j]
            possible_pin = ()
            for i in range(self.BOARDLENGTH):
                end_row, end_column = start_row + change_row * i, start_col + change_column * i
                if self.inside_board(end_row, end_column):
                    end_piece = self.board[end_row][end_column]
                    if end_piece[0] == ally and end_piece[1] != 'K':
                        if possible_pin == ():
                            possible_pin = (end_row, end_column, change_row, change_column)
                        else:
                            break
                    elif end_piece[0] == enemy:
                        piece_type = end_piece[1]
                        if (0 <= j <= 3 and piece_type == 'R') or \
                                (4 <= j <= 7 and piece_type == 'B') or \
                                (i == 1 and piece_type == 'p') and (
                                (enemy == 'w' and 6 <= j <= 7) or (enemy == 'b' and 4 <= j <= 5)) or \
                                (piece_type == 'Q') or (i == 1 and piece_type == 'K'):
                            if possible_pin == ():
                                in_check = True
                                checks.append((end_row, end_column, change_row, change_column))
                                break
                            else:
                                pins.append(possible_pin)
                                break
                        else:
                            break
        knight_directions = ((1, 2), (1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1), (-1, 2), (-1, -2))
        for change_row, change_column in knight_directions:
            end_row, end_column = start_row + change_row, start_col + change_column
            if self.inside_board(end_row, end_column):
                end_piece = self.board[end_row][end_column]
                if end_piece[0] == enemy and end_piece[1] == 'N':
                    in_check = True
                    checks.append((end_row, end_column, change_row, change_column))
        return in_check, pins, checks

    def update_castle_rights(self, move):
        if move.pieceMoved == 'wK':
            self.castleRights.wks = False
            self.castleRights.wqs = False
        elif move.pieceMoved == 'bK':
            self.castleRights.bks = False
            self.castleRights.bqs = False
        elif move.pieceMoved == 'wR':
            if move.startRow == 7:
                if move.startColumn == 0:
                    self.castleRights.wqs = False
                elif move.startColumn == 7:
                    self.castleRights.wks = False
        elif move.pieceMoved == 'bR':
            if move.startRow == 0:
                if move.startColumn == 0:
                    self.castleRights.bqs = False
                elif move.startColumn == 7:
                    self.castleRights.bks = False
        elif move.pieceCaptured == 'wR':
            if move.endRow == 7:
                if move.endColumn == 0:
                    self.castleRights.wqs = False
                elif move.endColumn == 7:
                    self.castleRights.wks = False
        elif move.pieceCaptured == 'bR':
            if move.endRow == 0:
                if move.endColumn == 0:
                    self.castleRights.bqs = False
                elif move.endColumn == 7:
                    self.castleRights.bks = False

    def get_castle_moves(self, row, column, moves):
        if self.inChecked:
            return
        if (self.whiteToMove and self.castleRights.wks) or (not self.whiteToMove and self.castleRights.bks):
            self.get_king_side_castle_moves(row, column, moves)
        if (self.whiteToMove and self.castleRights.wqs) or (not self.whiteToMove and self.castleRights.bqs):
            self.get_queen_side_castle_moves(row, column, moves)

    def square_under_attack(self, row, column):
        self.change_turn()
        opponent_moves = self.get_all_possible_moves()
        self.change_turn()
        for move in opponent_moves:
            if move.endRow == row and move.endColumn == column:
                return True
        return False

    def get_king_side_castle_moves(self, row, column, moves):
        if self.board[row][column + 1] == '--' and self.board[row][column + 2] == '--':
            if not self.square_under_attack(row, column + 1) and not self.square_under_attack(row, column + 2):
                moves.append(Move((row, column), (row, column + 2), self.board, is_castle=True))

    def get_queen_side_castle_moves(self, row, column, moves):
        if self.board[row][column - 1] == '--' and self.board[row][column - 2] == '--' and self.board[row][
            column - 3] == '--':
            if not self.square_under_attack(row, column - 1) and not self.square_under_attack(row, column - 2):
                moves.append(Move((row, column), (row, column - 2), self.board, is_castle=True))


class CastleRight:
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs

    def __repr__(self):
        return f"{self.wks=}, {self.bks=}, {self.wqs=}, {self.bks=}"


class Move:
    ranksToRows = {'8': 0, '7': 1, '6': 2, '5': 3, '4': 4, '3': 5, '2': 6, '1': 7}
    rowsToRanks = {0: '8', 1: '7', 2: '6', 3: '5', 4: '4', 5: '3', 6: '2', 7: '1'}
    filesToColumns = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
    columnsToFiles = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'}

    def __init__(self, starting_square, target_square, board, is_enpassant=False, is_castle=False):
        self.startRow, self.startColumn = starting_square
        self.endRow, self.endColumn = target_square
        self.pieceMoved = board[self.startRow][self.startColumn]
        self.pieceCaptured = board[self.endRow][self.endColumn]
        self.isPromotion = False
        self.isPromotion = (self.pieceMoved == 'wp' and target_square[0] == 0) or \
                           (self.pieceMoved == 'bp' and target_square[0] == 7)
        self.promotionPiece = None
        self.isEnPassant = is_enpassant
        self.isCastle = is_castle
        self.moveId = self.startRow * 1000 + self.startColumn * 100 + self.endRow * 10 + self.endColumn

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveId == other.moveId
        return False

    def __str__(self):
        #castle
        if self.isCastle:
            return '0-0' if self.endColumn == 6 else '0-0-0'
        end_square = self.get_rank_file(self.endRow, self.endColumn)
        if self.pieceMoved[1] == 'p':
            if self.pieceCaptured != '--':
                return f"{self.columnsToFiles[self.startColumn]}x{end_square}"
            elif self.isPromotion:
                pass
            else:
                return end_square
        return self.pieceMoved[1] + end_square



    def get_chess_notation(self):
        return self.get_rank_file(self.startRow, self.startColumn) + self.get_rank_file(self.endRow, self.endColumn)

    def get_rank_file(self, row, column):
        return self.columnsToFiles[column] + self.rowsToRanks[row]
