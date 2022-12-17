# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import copy
from typing import NamedTuple

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
        self.board[move.start_row][move.start_column] = '--'
        self.board[move.end_row][move.end_column] = move.promotionPiece if move.promotion else move.moved_piece
        if move.isEnPassant:
            self.board[move.start_row][move.end_column] = '--'
        elif move.isCastle:
            rook_position = move.end_column + (-1 if move.end_column - move.start_column == 2 else 1)
            corner_position = move.end_column + (1 if move.end_column - move.start_column == 2 else -2)
            self.board[move.end_row][rook_position] = self.board[move.end_row][corner_position]
            self.board[move.end_row][corner_position] = '--'
        self.states.update_states(move)

    def undo_move(self):
        if not self.states.move_logs:
            return None
        last_move = self.states.undo()
        self.board[last_move.end_row][last_move.end_column] = last_move.captured
        self.board[last_move.start_row][last_move.start_column] = last_move.moved_piece
        if last_move.isEnPassant:
            self.board[last_move.start_row][last_move.end_column] = self.states.opponent + 'p'
        elif last_move.isCastle:
            rook_position = last_move.end_column + (-1 if last_move.end_column - last_move.start_column == 2 else 1)
            corner_position = last_move.end_column + (1 if last_move.end_column - last_move.start_column == 2 else -2)
            self.board[last_move.end_row][corner_position] = self.board[last_move.end_row][rook_position]
            self.board[last_move.end_row][rook_position] = '--'

    def get_valid_moves(self):
        possible_moves = []
        self.states.check_for_pins_and_checks(self.board)
        king_row, king_column = self.states.king_position
        if self.states.checked:
            if len(self.states.checks) == 1:
                check = self.states.checks[0]
                possible_moves = self.get_all_possible_moves()
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
                    if possible_moves[i].moved_piece[1] != 'K':
                        if not (possible_moves[i].end_row, possible_moves[i].end_column) in valid_squares:
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
        for pin in self.states.pins:
            if (pin[0], pin[1]) == (row, column):
                pinned = True
                pin_direction = pin[2], pin[3]
                self.states.pins.remove(pin)
        return pinned, pin_direction

    def get_all_possible_moves(self):
        moves = []
        for row, boardRow in enumerate(self.board):
            for column, piece in enumerate(boardRow):
                if piece[0] == self.states.player:
                    self.moveFunctions[piece[1]](row, column, moves)
        return moves

    def get_pawn_moves(self, row, column, moves):
        piece_pinned, pin_direction = self.is_pinned(row, column)
        direction = -1 if self.states.white_to_move else 1
        capture = self.states.opponent
        double_jump = 6 if self.states.white_to_move else 1
        king_row, king_column = self.states.king_position

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
                    blocking_piece = attacking_piece = False
                    if king_row == row:
                        if king_column < column:
                            inside_range = range(king_column + 1, column - 1)
                            outside_range = range(column + 1, 8)
                        else:
                            inside_range = range(king_column - 1, column, -1)
                            outside_range = range(column - 2, -1, -1)
                        for i in inside_range:
                            if self.board[row][i] != '--':
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[row][i]
                            if square[0] == capture and (square[1] in ('R', 'Q')):
                                attacking_piece = True
                            elif square != '--':
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move((row, column), (row + direction, column - 1), self.board, is_enpassant=True))
        if column + 1 < BOARDLENGTH:
            if not piece_pinned or pin_direction == (direction, 1):
                if self.is_piece(row + direction, column + 1, capture):
                    moves.append(Move((row, column), (row + direction, column + 1), self.board))
                elif (row + direction, column + 1) == self.states.enpassant_possible:
                    blocking_piece = attacking_piece = False
                    if king_row == row:
                        if king_column < column:
                            inside_range = range(king_column + 1, column)
                            outside_range = range(column + 2, 8)
                        else:
                            inside_range = range(king_column - 1, column + 1, -1)
                            outside_range = range(column - 1, -1, -1)
                        for i in inside_range:
                            if self.board[row][i] != '--':
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[row][i]
                            if square[0] == capture and (square[1] in ('R', 'Q')):
                                attacking_piece = True
                            elif square != '--':
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move((row, column), (row + direction, column + 1), self.board, is_enpassant=True))

    def get_rook_moves(self, row, column, moves):
        piece_pinned, pin_direction = self.is_pinned(row, column)
        for change_row, change_column in ROOK_DIRECTIONS:
            if self.is_piece_movable(piece_pinned, pin_direction, (change_row, change_column)):
                for i in range(1, BOARDLENGTH):
                    end_row, end_column = row + change_row * i, column + change_column * i
                    if inside_board(end_row, end_column):
                        if self.is_empty_square(end_row, end_column):
                            moves.append(Move((row, column), (end_row, end_column), self.board))
                        elif self.is_piece(end_row, end_column, self.states.opponent):
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
        for change_row, change_column in KNIGHT_DIRECTIONS:
            end_row, end_column = row + change_row, column + change_column
            if inside_board(end_row, end_column):
                if self.is_empty_square(end_row, end_column) or self.is_piece(end_row, end_column,
                                                                              self.states.opponent):
                    moves.append(Move((row, column), (end_row, end_column), self.board))

    def get_bishop_moves(self, row, column, moves):
        piece_pinned, pin_direction = self.is_pinned(row, column)
        for change_row, change_column in BISHOP_DIRECTIONS:
            if self.is_piece_movable(piece_pinned, pin_direction, (change_row, change_column)):
                for i in range(1, BOARDLENGTH):
                    end_row, end_column = row + change_row * i, column + change_column * i
                    if inside_board(end_row, end_column):
                        if self.is_empty_square(end_row, end_column):
                            moves.append(Move((row, column), (end_row, end_column), self.board))
                        elif self.is_piece(end_row, end_column, self.states.opponent):
                            moves.append(Move((row, column), (end_row, end_column), self.board))
                            break
                        else:
                            break
                    else:
                        break

    def get_queen_moves(self, row, column, moves):
        piece_pinned, pin_direction = self.is_pinned(row, column)
        capture = self.states.opponent
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
                if end_piece[0] != self.states.player:
                    self.states.update_king(end_row, end_column)
                    self.board[end_row][end_column] = '--'
                    in_checked, pins, checks = self.states.checked, copy.deepcopy(self.states.pins), copy.deepcopy(
                        self.states.checks)
                    self.states.check_for_pins_and_checks(self.board)
                    self.board[end_row][end_column] = end_piece
                    if not self.states.checked:
                        moves.append(Move((row, column), (end_row, end_column), self.board))
                    self.states.update_king(row, column)
                    self.states.checked = in_checked
                    self.states.pins = copy.deepcopy(pins)
                    self.states.checks = copy.deepcopy(checks)

    def get_castle_moves(self, row, column, moves):
        if self.states.checked:
            return
        if getattr(self.states.castle_rights, self.states.player + "ks"):
            self.get_king_side_castle_moves(row, column, moves)
        if getattr(self.states.castle_rights, self.states.player + "qs"):
            self.get_queen_side_castle_moves(row, column, moves)

    def square_under_attack(self, row, column):
        self.states.change_turn()
        opponent_moves = self.get_all_possible_moves()
        self.states.change_turn()
        for move in opponent_moves:
            if move.end_row == row and move.end_column == column:
                return True
        return False

    def get_king_side_castle_moves(self, row, column, moves):
        if self.is_empty_square(row, column + 1) and self.is_empty_square(row, column + 2):
            if not self.square_under_attack(row, column + 1) and not self.square_under_attack(row, column + 2):
                moves.append(Move((row, column), (row, column + 2), self.board, is_castle=True))

    def get_queen_side_castle_moves(self, row, column, moves):
        if self.is_empty_square(row, column - 1) and self.is_empty_square(row, column - 2) \
                and self.is_empty_square(row, column - 3):
            if not self.square_under_attack(row, column - 1) and not self.square_under_attack(row, column - 2):
                moves.append(Move((row, column), (row, column - 2), self.board, is_castle=True))

    def is_empty_square(self, row, column):
        return self.board[row][column] == '--'

    def is_piece(self, row, column, color, piece_type=None):
        return self.board[row][column][0] == color and (
            self.board[row][column][1] == piece_type if piece_type is not None else True)

    def is_piece_movable(self, pinned, pin_direction, move_direction):
        return not pinned or (pin_direction in (move_direction, (-move_direction[0], -move_direction[1])))


class CastleRights(NamedTuple):
    wks: bool
    bks: bool
    wqs: bool
    bqs: bool


class KingPosition(NamedTuple):
    white_king: tuple
    black_king: tuple


class GameStatus(NamedTuple):
    checked: bool
    pins: list
    checks: list


class StateLog:
    def __init__(self):
        self.enpassant_possible = ()
        self.enpassant_logs = [self.enpassant_possible]
        self.move_logs = []
        self.castle_rights = CastleRights(True, True, True, True)
        self.castle_rights_logs = [self.castle_rights]
        self._checkmate = False
        self._stalemate = False
        self.white_to_move = True
        self.is_checked = False
        self.pins = []
        self.checks = []
        self.kings_position = KingPosition((7, 4), (0, 4))

    def change_turn(self):
        self.white_to_move = not self.white_to_move

    def update_states(self, move):
        self.move_logs.append(move)
        if move.moved_piece[1] == 'K':
            self.update_king(move.end_row, move.end_column)
        if move.moved_piece[1] == 'p' and abs(move.start_row - move.end_row) == 2:
            self.enpassant_possible = ((move.start_row + move.end_row) // 2, move.start_column)
        else:
            self.enpassant_possible = ()
        self.enpassant_logs.append(self.enpassant_possible)
        self.update_castle_rights(move)
        self.castle_rights_logs.append(self.castle_rights)
        self.change_turn()

    def update_castle_rights(self, move):
        wks, wqs, bks, bqs = self.castle_rights
        if move.moved_piece == 'wK':
            wks = wqs = False
        elif move.moved_piece == 'bK':
            bks = bqs = False
        elif move.moved_piece == 'wR' or move.captured == 'wR':
            considered_row = move.start_row if move.moved_piece == 'wR' else move.end_row
            considered_column = move.start_column if move.moved_piece == 'wR' else move.end_column
            wqs = not (considered_row == 7 and considered_row == 0)
            wks = not (considered_row == 7 and considered_column == 7)
        elif move.moved_piece == 'bR' or move.captured == 'bR':
            considered_row = move.start_row if move.moved_piece == 'bR' else move.end_row
            considered_column = move.start_column if move.moved_piece == 'bR' else move.end_column
            bqs = not (considered_row == 0 and considered_column == 0)
            bks = not (considered_row == 0 and considered_column == 7)
        self.castle_rights = CastleRights(wks, bks, wqs, bqs)

    def undo(self):
        self.update_mate(1)
        self.change_turn()
        self.enpassant_logs.pop()
        self.enpassant_possible = self.enpassant_logs[-1]
        self.castle_rights_logs.pop()
        self.castle_rights = self.castle_rights_logs[-1]
        last_move = self.move_logs[-1]
        if last_move.moved_piece[1] == 'K':
            self.update_king(last_move.start_row, last_move.start_column)
        return self.move_logs.pop()

    def check_for_pins_and_checks(self, board):
        pins, checks, in_check = [], [], False
        enemy, ally = self.opponent, self.player
        start_row, start_col = self.king_position
        directions = ROOK_DIRECTIONS + BISHOP_DIRECTIONS
        for j in range(len(directions)):
            change_row, change_column = directions[j]
            possible_pin = ()
            for i in range(1, BOARDLENGTH):
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

        self.checked = in_check
        self.pins = copy.deepcopy(pins)
        self.checks = copy.deepcopy(checks)

    def update_mate(self, param):
        self.checkmate = param == 0 and self.checked
        self.stalemate = param == 0 and not self.checked

    def update_king(self, row, column):
        white_king = (row, column) if self.white_to_move else self.kings_position.white_king
        black_king = (row, column) if not self.white_to_move else self.kings_position.black_king
        self.kings_position = KingPosition(white_king, black_king)

    @property
    def checked(self):
        return self.is_checked

    @checked.setter
    def checked(self, value):
        if value is bool:
            self.is_checked = value

    @property
    def checkmate(self):
        return self._checkmate

    @checkmate.setter
    def checkmate(self, value):
        if value is bool:
            self.checkmate = value

    @property
    def stalemate(self):
        return self._stalemate

    @stalemate.setter
    def stalemate(self, value):
        if value is bool:
            self.stalemate = value

    @property
    def player(self):
        return 'w' if self.white_to_move else 'b'

    @property
    def opponent(self):
        return 'b' if self.white_to_move else 'w'

    @property
    def king_position(self):
        king = 'white_king' if self.white_to_move else 'black_king'
        return getattr(self.kings_position, king)


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
