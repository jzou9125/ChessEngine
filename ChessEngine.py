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
        self.board[move.startRow][move.startColumn] = '--'
        self.board[move.endRow][move.endColumn] = move.promotionPiece if move.promotion else move.piece_moved
        if move.isEnPassant:
            self.board[move.startRow][move.endColumn] = '--'
        elif move.isCastle:
            rook_position = move.endColumn + (-1 if move.endColumn - move.startColumn == 2 else 1)
            corner_position = move.endColumn + (1 if move.endColumn - move.startColumn == 2 else -2)
            self.board[move.endRow][rook_position] = self.board[move.endRow][corner_position]
            self.board[move.endRow][corner_position] = '--'
        self.states.update_states(move)

    def undo_move(self):
        if not self.states.move_logs:
            return None
        last_move = self.states.undo()
        self.board[last_move.endRow][last_move.endColumn] = last_move.piece_captured
        self.board[last_move.startRow][last_move.startColumn] = last_move.piece_moved
        if last_move.isEnPassant:
            self.board[last_move.startRow][last_move.endColumn] = self.states.opponent + 'p'
        elif last_move.isCastle:
            rook_position = last_move.endColumn + (-1 if last_move.endColumn - last_move.startColumn == 2 else 1)
            corner_position = last_move.endColumn + (1 if last_move.endColumn - last_move.startColumn == 2 else -2)
            self.board[last_move.endRow][corner_position] = self.board[last_move.endRow][rook_position]
            self.board[last_move.endRow][rook_position] = '--'

    def get_valid_moves(self):
        possible_moves = []
        self.states.check_for_pins_and_checks(self.board)
        king_row, king_column = self.states.king_position
        if self.states.is_checked:
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
                    if possible_moves[i].piece_moved[1] != 'K':
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
                    self.states.check_for_pins_and_checks(self.board)
                    self.board[end_row][end_column] = end_piece
                    if not self.states.is_checked:
                        moves.append(Move((row, column), (end_row, end_column), self.board))
                    self.states.update_king(row, column)

    def get_castle_moves(self, row, column, moves):
        if self.states.is_checked:
            return
        if getattr(self.states.castle_rights, self.states.player + 'ks'):
            self.get_king_side_castle_moves(row, column, moves)
        if getattr(self.states.castle_rights, self.states.player + 'qs'):
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


class StateLog:
    def __init__(self):
        self.enpassant_possible = ()
        self.enpassant_logs = [self.enpassant_possible]
        self.move_logs = []
        self.castle_rights = CastleRights(True, True, True, True)
        self.castle_rights_logs = [self.castle_rights]
        self.checkmate = False
        self.stalemate = False
        self.white_to_move = True
        self._player = 'w'
        self._opponent = 'b'
        self.is_checked = False
        self.pins = []
        self.checks = []
        self._king_position = KingPosition((7, 4), (0, 4))

    def change_turn(self):
        self.white_to_move = not self.white_to_move
        self._player = 'b' if self.player == 'w' else 'w'
        self._opponent = 'w' if self.opponent == 'b' else 'b'

    def update_states(self, move):
        self.move_logs.append(move)
        if move.piece_moved[1] == 'K':
            self.update_king(move.endRow, move.endColumn)
        if move.piece_moved[1] == 'p' and abs(move.startRow - move.endRow) == 2:
            self.enpassant_possible = ((move.startRow + move.endRow) // 2, move.startColumn)
        else:
            self.enpassant_possible = ()
        self.enpassant_logs.append(self.enpassant_possible)
        self.update_castle_rights(move)
        self.castle_rights_logs.append(self.castle_rights)
        self.change_turn()

    def update_castle_rights(self, move):
        wks, wqs, bks, bqs = self.castle_rights
        if move.piece_moved == 'wK':
            wks = wqs = False
        elif move.piece_moved == 'bK':
            bks = bqs = False
        elif move.piece_moved == 'wR' or move.piece_captured == 'wR':
            considered_row = move.startRow if move.piece_moved == 'wR' else move.endRow
            considered_column = move.startColumn if move.piece_moved == 'wR' else move.endColumn
            if considered_row == 7:
                if considered_column == 0:
                    wqs = False
                elif considered_column == 7:
                    wks = False
        elif move.piece_moved == 'bR' or move.piece_captured == 'bR':
            considered_row = move.startRow if move.piece_moved == 'bR' else move.endRow
            considered_column = move.startColumn if move.piece_moved == 'bR' else move.endColumn
            if considered_row == 0:
                if considered_column == 0:
                    bqs = False
                elif considered_column == 7:
                    bks = False
        self.castle_rights = CastleRights(wks, bks, wqs, bqs)

    def undo(self):
        self.update_mate(1)
        self.change_turn()
        self.enpassant_logs.pop()
        self.enpassant_possible = self.enpassant_logs[-1]
        self.castle_rights_logs.pop()
        self.castle_rights = self.castle_rights_logs[-1]
        last_move = self.move_logs[-1]
        if last_move.piece_moved[1] == 'K':
            self.update_king(last_move.startRow, last_move.startColumn)
        return self.move_logs.pop()

    def check_for_pins_and_checks(self, board):
        pins, checks, in_check = [], [], False
        enemy, ally = self.opponent, self.player
        start_row, start_col = self.opponent_king
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
        self.pins = copy.deepcopy(pins)
        self.checks = copy.deepcopy(checks)

    def update_mate(self, param):
        stalemate, checkmate = False, False
        if param == 0:
            if self.is_checked:
                checkmate = True
            else:
                stalemate = True
        self.checkmate = checkmate
        self.stalemate = stalemate

    def update_king(self, row, column):
        white_king = (row, column) if self.white_to_move else self.king_position
        black_king = (row, column) if not self.white_to_move else self._king_position.black_king
        self._king_position = KingPosition(white_king, black_king)

    @property
    def player(self):
        return self._player

    @property
    def opponent(self):
        return self._opponent

    @property
    def opponent_king(self):
        king = 'white_king' if not self.white_to_move else 'black_king'
        return getattr(self._king_position, king)

    @property
    def king_position(self):
        king = 'white_king' if self.white_to_move else 'black_king'
        return getattr(self._king_position, king)


class Move:
    ranksToRows = {'8': 0, '7': 1, '6': 2, '5': 3, '4': 4, '3': 5, '2': 6, '1': 7}
    rowsToRanks = {0: '8', 1: '7', 2: '6', 3: '5', 4: '4', 5: '3', 6: '2', 7: '1'}
    filesToColumns = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
    columnsToFiles = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'}

    def __init__(self, starting_square, target_square, board, is_enpassant=False, is_castle=False):
        self.startRow, self.startColumn = starting_square
        self.endRow, self.endColumn = target_square
        self._piece_moved = board[self.startRow][self.startColumn]
        self._piece_captured = board[self.endRow][self.endColumn]
        self._is_promotion = (self._piece_moved == 'wp' and target_square[0] == 0) or \
                         (self._piece_moved == 'bp' and target_square[0] == 7)
        self.promotionPiece = None
        self.isEnPassant = is_enpassant
        self.isCastle = is_castle

    @property
    def piece_captured(self):
        return self._piece_captured

    @property
    def piece_moved(self):
        return self._piece_moved

    @property
    def promotion(self):
        return self._is_promotion

    def __str__(self):
        if self.isCastle:
            return '0-0' if self.endColumn == 6 else '0-0-0'
        end_square = self.get_rank_file(self.endRow, self.endColumn)
        if self._piece_moved[1] == 'p':
            if self.piece_captured != '--':
                return f"{self.columnsToFiles[self.startColumn]}x{end_square}"
            elif self.promotion:
                pass
            else:
                return end_square
        return f"{self._piece_moved[1]}{'x' if self.piece_captured != '--' else ''}{end_square}"

    def get_rank_file(self, row, column):
        return self.columnsToFiles[column] + self.rowsToRanks[row]
