# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import copy
import States
from Move import Move
from Board import Board
from dataclasses import dataclass

BOARDLENGTH = 8
KNIGHT_DIRECTIONS = ((1, 2), (1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1), (-1, 2), (-1, -2))
ROOK_DIRECTIONS = ((1, 0), (0, 1), (-1, 0), (0, -1))
BISHOP_DIRECTIONS = ((1, 1), (-1, -1), (1, -1), (-1, 1))


def inside_board(row, column):
    return row in range(BOARDLENGTH) and column in range(BOARDLENGTH)



class GameState:
    def __init__(self):
        self.board = Board()
        self.moveFunctions = {'p': self.get_pawn_moves, 'R': self.get_rook_moves, 'N': self.get_knight_moves,
                              'B': self.get_bishop_moves, 'Q': self.get_queen_moves, 'K': self.get_king_moves}
        self.states = State()





    def undo_move(self):
        if not self.states.move_logs:
            return None
        last_move = self.states.undo()
        self.board.get(last_move.end_row, last_move.end_column).board_value = last_move.captured
        self.board.get(last_move.start_row, last_move.start_column).board_value = last_move.moved_piece
        if last_move.isEnPassant:
            self.board.get(last_move.start_row, last_move.end_column).board_value = self.states.opponent + 'p'
        elif last_move.isCastle:
            rook_position = last_move.end_column + (-1 if last_move.end_column - last_move.start_column == 2 else 1)
            corner_position = last_move.end_column + (1 if last_move.end_column - last_move.start_column == 2 else -2)
            self.board.get(last_move.end_row, corner_position).board_value = self.board.get(last_move.end_row, rook_position).board_value
            self.board.get(last_move.end_row, rook_position).board_value = '--'

    def get_valid_moves(self):
        possible_moves = []
        self.states.check_for_pins_and_checks(self.board)
        king_row, king_column = self.states.king_position
        if self.states.checked:
            if len(self.states.checks) == 1:
                check = self.states.checks[0]
                possible_moves = self.get_all_possible_moves()
                check_row, check_column = check[0], check[1]
                piece_checking = self.board.get(check_row, check_column)
                valid_squares = []
                if piece_checking.chess_piece == 'N':
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

        print(possible_moves)
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
        for row, boardRow in enumerate(self.board.board):
            for column, piece in enumerate(boardRow):
                if piece.color == self.states.player:
                    self.moveFunctions[piece.chess_piece](piece.row, piece.column, moves)
        return moves

    def get_pawn_moves(self, row, column, moves):
        piece_pinned, pin_direction = self.is_pinned(row, column)
        direction = -1 if self.states.white_to_move else 1
        capture = self.states.opponent
        double_jump = 6 if self.states.white_to_move else 1
        king_row, king_column = self.states.king_position

        if self.board.get(row+direction, column).is_empty:
            if not piece_pinned or pin_direction == (direction, 0):
                moves.append(Move((row, column), (row + direction, column), self.board))
                if row == double_jump and self.board.get(row+direction*2, column).is_empty:
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
                            if not self.board.get(row, i).is_empty:
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board.get(row, i)
                            if square.color == capture and (square.chess_piece in ('R', 'Q')):
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
                            if not self.board.get(row, i).is_empty:
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board.get(row, i)
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
                        if self.board.get(end_row, end_column).is_empty:
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
                if self.board.get(end_row, end_column).is_empty or self.is_piece(end_row, end_column,
                                                                              self.states.opponent):
                    moves.append(Move((row, column), (end_row, end_column), self.board))

    def get_bishop_moves(self, row, column, moves):
        piece_pinned, pin_direction = self.is_pinned(row, column)
        for change_row, change_column in BISHOP_DIRECTIONS:
            if self.is_piece_movable(piece_pinned, pin_direction, (change_row, change_column)):
                for i in range(1, BOARDLENGTH):
                    end_row, end_column = row + change_row * i, column + change_column * i
                    if inside_board(end_row, end_column):
                        if self.board.get(end_row, end_column).is_empty:
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
                        if self.board.get(end_row, end_column).is_empty:
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
                end_piece = self.board.get(end_row, end_column)
                if end_piece.color != self.states.player:
                    self.states.update_king(end_row, end_column)
                    self.board.get(end_row, end_column).board_value = '--'
                    in_checked, pins, checks = self.states.checked, copy.deepcopy(self.states.pins), copy.deepcopy(
                        self.states.checks)
                    self.states.check_for_pins_and_checks(self.board)
                    self.board.get(end_row, end_column).board_value = end_piece
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
        if self.board.get(row, column+1).is_empty and self.board.get(row, column+2).is_empty:
            if not self.square_under_attack(row, column + 1) and not self.square_under_attack(row, column + 2):
                moves.append(Move((row, column), (row, column + 2), self.board, is_castle=True))

    def get_queen_side_castle_moves(self, row, column, moves):
        if self.board.get(row, column-1).is_empty and self.board.get(row, column-2).is_empty and self.board.get(row, column-3).is_empty:
            if not self.square_under_attack(row, column - 1) and not self.square_under_attack(row, column - 2):
                moves.append(Move((row, column), (row, column - 2), self.board, is_castle=True))

    def is_piece(self, row, column, color, piece_type=None):
        return self.board.get(row, column).color == color and (
            self.board.get(row, column).chess_piece == piece_type if piece_type is not None else True)

    def is_piece_movable(self, pinned, pin_direction, move_direction):
        return not pinned or (pin_direction in (move_direction, (-move_direction[0], -move_direction[1])))


@dataclass
class KingPosition():
    white_king: tuple = (7, 4)
    black_king: tuple = (0, 4)


class State:
    def __init__(self):
        self.logs = States.StatesLogging()
        self._checkmate = False
        self._stalemate = False
        self.white_to_move = True
        self.is_checked = False
        self.pins = []
        self.checks = []
        self.kings_position = KingPosition()

    def change_turn(self):
        self.white_to_move = not self.white_to_move

    def update_states(self, move):
        self.logs.update(move)
        if move.moved_piece[1] == 'K':
            self.update_king(move.end_row, move.end_column)
        self.change_turn()

    def undo(self):
        self.update_mate(1)
        self.change_turn()
        last_move = self.logs.undo()
        if last_move.moved_piece[1] == 'K':
            self.update_king(last_move.start_row, last_move.start_column)
        return last_move

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
                    end_piece = board.get(end_row, end_column)
                    if end_piece.color == ally and end_piece.chess_piece != 'K':
                        if possible_pin == ():
                            possible_pin = (end_row, end_column, change_row, change_column)
                        else:
                            break
                    elif end_piece.color == enemy:
                        piece_type = end_piece.chess_piece
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
                end_piece = board.get(end_row, end_column)
                if end_piece.color == enemy and end_piece.chess_piece == 'K':
                    in_check = True
                    checks.append((end_row, end_column, change_row, change_column))

        self.checked = in_check
        self.pins = copy.deepcopy(pins)
        self.checks = copy.deepcopy(checks)

    def update_mate(self, param):
        self.checkmate = param == 0 and self.checked
        self.stalemate = param == 0 and not self.checked

    def update_king(self, row, column):
        king = 'white_king' if self.white_to_move else 'black_king'
        setattr(self.kings_position, king, (row, column))

    @property
    def enpassant_possible(self):
        return self.logs.enpassant_possible

    @property
    def castle_rights(self):
        return self.logs.castle_rights

    @property
    def move_logs(self):
        return self.logs.moves

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
