# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import copy

BOARDLENGTH = 8
KNIGHT_DIRECTIONS = ((1, 2), (1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1), (-1, 2), (-1, -2))
ROOK_DIRECTIONS = ((1, 0), (0, 1), (-1, 0), (0, -1))
BISHOP_DIRECTIONS = ((1, 1), (-1, -1), (1, -1), (-1, 1))


def inside_board(row, column):
    return row in range(BOARDLENGTH) and column in range(BOARDLENGTH)


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
        self.states = StateLog()

    def process_move(self, move):
        self.board[move.startRow][move.startColumn] = '--'
        self.board[move.endRow][move.endColumn] = move.promotionPiece if move.isPromotion else move.pieceMoved
        if move.isEnPassant:
            self.board[move.startRow][move.endColumn] = '--'
        elif move.isCastle:
            if move.endColumn - move.startColumn == 2:
                self.board[move.endRow][move.endColumn - 1] = self.board[move.endRow][move.endColumn + 1]
                self.board[move.endRow][move.endColumn + 1] = '--'
            else:
                self.board[move.endRow][move.endColumn + 1] = self.board[move.endRow][move.endColumn - 2]
                self.board[move.endRow][move.endColumn - 2] = '--'
        self.states.update_states(move)

    def undo_move(self):
        if not self.states.move_logs:
            return None
        last_move = self.states.undo()
        self.board[last_move.endRow][last_move.endColumn] = last_move.pieceCaptured
        self.board[last_move.startRow][last_move.startColumn] = last_move.pieceMoved
        if last_move.isEnPassant:
            self.board[last_move.startRow][last_move.endColumn] = self.states.opponent_color() + 'p'
        elif last_move.isCastle:
            if last_move.endColumn - last_move.startColumn == 2:
                self.board[last_move.endRow][last_move.endColumn + 1] = self.board[last_move.endRow][
                    last_move.endColumn - 1]
                self.board[last_move.endRow][last_move.endColumn - 1] = '--'
            else:
                self.board[last_move.endRow][last_move.endColumn - 2] = self.board[last_move.endRow][
                    last_move.endColumn + 1]
                self.board[last_move.endRow][last_move.endColumn + 1] = '--'

    def get_valid_moves(self):
        possible_moves = []
        self.states.check_for_pins_and_checks(self.board)
        king_row, king_column = self.states.get_king_position()
        if self.states.is_checked:
            if len(self.states.checks) == 1:
                possible_moves = self.get_all_possible_moves()
                check = self.states.checks[0]
                check_row, check_column = check[0], check[1]
                piece_checking = self.board[check_row][check_column]
                valid_squares = []
                if piece_checking[1] == 'N':
                    valid_squares = [(check_row, check_column)]
                else:
                    for i in range(1, BOARDLENGTH):
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

        self.states.update_mate(len(possible_moves))
        return possible_moves

    def is_pinned(self, row, column):
        pinned, pin_direction = False, ()
        for i in range(len(self.states.pins) - 1, -1, -1):
            if self.states.pins[i][0] == row and self.states.pins[i][1] == column:
                pinned = True
                pin_direction = self.states.pins[i][2], self.states.pins[i][3]
                self.states.pins.remove(self.states.pins[i])
        return pinned, pin_direction

    def get_all_possible_moves(self):
        moves = []
        for row, boardRow in enumerate(self.board):
            for column, piece in enumerate(boardRow):
                if piece[0] == self.states.player_color():
                    self.moveFunctions[piece[1]](row, column, moves)
        return moves

    def get_pawn_moves(self, row, column, moves):
        piece_pinned, pin_direction = self.is_pinned(row, column)
        direction = -1 if self.states.white_to_move else 1
        capture = self.states.opponent_color()
        double_jump = 6 if self.states.white_to_move else 1

        if self.is_empty_square(row + direction, column):
            if not piece_pinned or pin_direction == (direction, 0):
                moves.append(Move((row, column), (row + direction, column), self.board))
                if row == double_jump and self.is_empty_square(row + direction * 2, column):
                    moves.append(Move((row, column), (row + direction * 2, column), self.board))
        if column - 1 >= 0:
            if not piece_pinned or pin_direction == (direction, -1):
                if self.is_piece(row + direction, column - 1, capture):
                    moves.append(Move((row, column), (row + direction, column - 1), self.board))
                elif (row + direction, column - 1) == self.states.enpassant_possible:
                    moves.append(Move((row, column), (row + direction, column - 1), self.board, is_enpassant=True))
        if column + 1 < BOARDLENGTH:
            if not piece_pinned or pin_direction == (direction, 1):
                if self.is_piece(row + direction, column + 1, capture):
                    moves.append(Move((row, column), (row + direction, column + 1), self.board))
                elif (row + direction, column + 1) == self.states.enpassant_possible:
                    moves.append(Move((row, column), (row + direction, column + 1), self.board, is_enpassant=True))

    def get_rook_moves(self, row, column, moves):
        piece_pinned, pin_direction = self.is_pinned(row, column)
        capture = self.states.opponent_color()
        for change_row, change_column in ROOK_DIRECTIONS:
            if self.is_piece_movable(piece_pinned, pin_direction, (change_row, change_column)):
                for i in range(1, BOARDLENGTH):
                    end_row, end_column = row + change_row * i, column + change_column * i
                    if inside_board(end_row, end_column):
                        if self.is_empty_square(end_row, end_column):
                            moves.append(Move((row, column), (end_row, end_column), self.board))
                        elif self.is_piece(end_row, end_column, capture):
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
        capture = self.states.opponent_color()
        for change_row, change_column in KNIGHT_DIRECTIONS:
            end_row, end_column = row + change_row, column + change_column
            if inside_board(end_row, end_column):
                if self.is_empty_square(end_row, end_column) or self.is_piece(end_row, end_column, capture):
                    moves.append(Move((row, column), (end_row, end_column), self.board))

    def get_bishop_moves(self, row, column, moves):
        piece_pinned, pin_direction = self.is_pinned(row, column)
        capture = self.states.opponent_color()
        for change_row, change_column in BISHOP_DIRECTIONS:
            if self.is_piece_movable(piece_pinned, pin_direction, (change_row, change_column)):
                for i in range(1, BOARDLENGTH):
                    end_row, end_column = row + change_row * i, column + change_column * i
                    if inside_board(end_row, end_column):
                        if self.is_empty_square(end_row, end_column):
                            moves.append(Move((row, column), (end_row, end_column), self.board))
                        elif self.is_piece(end_row, end_column, capture):
                            moves.append(Move((row, column), (end_row, end_column), self.board))
                            break
                        else:
                            break
                    else:
                        break

    def get_queen_moves(self, row, column, moves):
        piece_pinned, pin_direction = self.is_pinned(row, column)
        capture = self.states.opponent_color()
        for change_row, change_column in ROOK_DIRECTIONS + BISHOP_DIRECTIONS:
            if self.is_piece_movable(piece_pinned, pin_direction, (change_row, change_column)):
                for i in range(1, BOARDLENGTH):
                    end_row, end_column = row + change_row * i, column + change_column * i
                    if inside_board(end_row, end_column):
                        if self.is_empty_square(end_row, end_column):
                            moves.append(Move((row, column), (end_row, end_column), self.board))
                        elif self.is_piece(end_row, end_column, capture):
                            moves.append(Move((row, column), (end_row, end_column), self.board))
                            break
                        else:
                            break
                    else:
                        break

    def get_king_moves(self, row, column, moves):
        for changeRow, changeColumn in ROOK_DIRECTIONS + BISHOP_DIRECTIONS:
            end_row, end_column = row + changeRow, column + changeColumn
            if inside_board(end_row, end_column):
                end_piece = self.board[end_row][end_column]
                if end_piece[0] != self.states.player_color():
                    self.states.update_king(end_row, end_column)
                    self.board[end_row][end_column] = '--'
                    self.states.check_for_pins_and_checks(self.board)
                    self.board[end_row][end_column] = end_piece
                    if not self.states.is_checked:
                        moves.append(Move((row, column), (end_row, end_column), self.board))
                    self.states.update_king(row, column)

    def get_castle_moves(self, row, column, moves):
        if self.states.is_checked:
            return
        if self.states.conditions_for_castle('ks'):
            self.get_king_side_castle_moves(row, column, moves)
        if self.states.conditions_for_castle('qs'):
            self.get_queen_side_castle_moves(row, column, moves)

    def square_under_attack(self, row, column):
        self.states.change_turn()
        opponent_moves = self.get_all_possible_moves()
        self.states.change_turn()
        for move in opponent_moves:
            if move.endRow == row and move.endColumn == column:
                return True
        return False

    def get_king_side_castle_moves(self, row, column, moves):
        if self.is_empty_square(row, column + 1) and self.is_empty_square(row, column + 2):
            if not self.square_under_attack(row, column + 1) and not self.square_under_attack(row, column + 2):
                moves.append(Move((row, column), (row, column + 2), self.board, is_castle=True))

    def get_queen_side_castle_moves(self, row, column, moves):
        if self.is_empty_square(row, column - 1) and self.is_empty_square(row, column - 2) and self.is_empty_square(row,
                                                                                                                    column - 3):
            if not self.square_under_attack(row, column - 1) and not self.square_under_attack(row, column - 2):
                moves.append(Move((row, column), (row, column - 2), self.board, is_castle=True))

    def is_empty_square(self, row, column):
        return self.board[row][column] == '--'

    def is_piece(self, row, column, color, piece_type=None):
        return self.board[row][column][0] == color and (
            self.board[row][column][1] == piece_type if piece_type is not None else True)

    def is_piece_movable(self, pinned, pin_direction, move_direction):
        return not pinned or (pin_direction in (move_direction, (-move_direction[0], -move_direction[1])))


class StateLog:
    def __init__(self):
        self.enpassant_possible = ()
        self.enpassant_logs = [self.enpassant_possible]
        self.move_logs = []
        self.castle_rights = {'wks': True, 'bks': True, 'wqs': True, 'bqs': True}
        self.castle_rights_logs = [copy.deepcopy(self.castle_rights)]
        self.checkmate = False
        self.stalemate = False
        self.white_to_move = True
        self.is_checked = False
        self.pins = []
        self.checks = []
        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)

    def player_color(self):
        return 'w' if self.white_to_move else 'b'

    def opponent_color(self):
        return 'b' if self.white_to_move else 'w'

    def change_turn(self):
        self.white_to_move = not self.white_to_move

    def update_states(self, move):
        if move.pieceMoved == 'wK':
            self.white_king_location = move.endRow, move.endColumn
        elif move.pieceMoved == 'bK':
            self.black_king_location = move.endRow, move.endColumn
        self.move_logs.append(move)
        if move.pieceMoved[1] == 'p' and abs(move.startRow - move.endRow) == 2:
            self.enpassant_possible = ((move.startRow + move.endRow) // 2, move.startColumn)
        else:
            self.enpassant_possible = ()
        self.enpassant_logs.append(self.enpassant_possible)
        self.update_castle_rights(move)
        self.castle_rights_logs.append(copy.deepcopy(self.castle_rights))
        self.change_turn()

    def update_castle_rights(self, move):
        if move.pieceMoved == 'wK':
            self.castle_rights['wks'] = False
            self.castle_rights['wqs'] = False
        elif move.pieceMoved == 'bK':
            self.castle_rights['bks'] = False
            self.castle_rights['bqs'] = False
        elif move.pieceMoved == 'wR':
            if move.startRow == 7:
                if move.startColumn == 0:
                    self.castle_rights['wqs'] = False
                elif move.startColumn == 7:
                    self.castle_rights['wks'] = False
        elif move.pieceMoved == 'bR':
            if move.startRow == 0:
                if move.startColumn == 0:
                    self.castle_rights['bqs'] = False
                elif move.startColumn == 7:
                    self.castle_rights['bks'] = False
        elif move.pieceCaptured == 'wR':
            if move.endRow == 7:
                if move.endColumn == 0:
                    self.castle_rights['wqs'] = False
                elif move.endColumn == 7:
                    self.castle_rights['wks'] = False
        elif move.pieceCaptured == 'bR':
            if move.endRow == 0:
                if move.endColumn == 0:
                    self.castle_rights['bqs'] = False
                elif move.endColumn == 7:
                    self.castle_rights['bks'] = False

    def undo(self):
        self.update_mate(1)
        self.change_turn()
        self.enpassant_logs.pop()
        self.enpassant_possible = self.enpassant_logs[-1]
        self.castle_rights_logs.pop()
        self.castle_rights = copy.deepcopy(self.castle_rights_logs[-1])
        last_move = self.move_logs[-1]
        if last_move.pieceMoved == 'wK':
            self.white_king_location = last_move.startRow, last_move.startColumn
        if last_move.pieceMoved == 'bK':
            self.black_king_location = last_move.startRow, last_move.startColumn
        return self.move_logs.pop()

    def conditions_for_castle(self, king_or_queen_side):
        castle_direction = ('w' if self.white_to_move else 'b') + king_or_queen_side
        return self.castle_rights[castle_direction]

    def check_for_pins_and_checks(self, board):
        pins, checks, in_check = [], [], False
        enemy, ally = self.opponent_color(), self.player_color()
        start_row, start_col = self.get_king_position()
        directions = ROOK_DIRECTIONS + BISHOP_DIRECTIONS
        for j in range(len(directions)):
            change_row, change_column = directions[j]
            possible_pin = ()
            for i in range(BOARDLENGTH):
                end_row, end_column = start_row + change_row * i, start_col + change_column * i
                if inside_board(end_row, end_column):
                    end_piece = board[end_row][end_column]
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
                else:
                    break

        for change_row, change_column in KNIGHT_DIRECTIONS:
            end_row, end_column = start_row + change_row, start_col + change_column
            if inside_board(end_row, end_column):
                end_piece = board[end_row][end_column]
                if end_piece[0] == enemy and end_piece[1] == 'K':
                    in_check = True
                    checks.append((end_row, end_column, change_row, change_column))

        self.is_checked = in_check
        self.pins = pins
        self.checks = checks

    def update_mate(self, param):
        if param == 0:
            if self.is_checked:
                self.checkmate = True
            else:
                self.stalemate = True

    def update_king(self, end_row, end_column):
        if self.white_to_move:
            self.white_king_location = end_row, end_column
        else:
            self.black_king_location = end_row, end_column

    def get_king_position(self):
        return self.white_king_location if self.white_to_move else self.black_king_location


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

    def __str__(self):
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

    def get_rank_file(self, row, column):
        return self.columnsToFiles[column] + self.rowsToRanks[row]
