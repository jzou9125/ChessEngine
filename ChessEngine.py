# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import copy
import States
from Move import Move, EnpassantMove, CastleMove
from Board import Board
from dataclasses import dataclass, field
from typing import Generator, Optional

BOARDLENGTH = 8
KNIGHT_DIRECTIONS = ((1, 2), (1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1), (-1, 2), (-1, -2))
ROOK_DIRECTIONS = ((1, 0), (0, 1), (-1, 0), (0, -1))
BISHOP_DIRECTIONS = ((1, 1), (-1, -1), (1, -1), (-1, 1))


def inside_board(row, column):
    return row in range(BOARDLENGTH) and column in range(BOARDLENGTH)


@dataclass
class Direction:
    row: int
    column: int
    direction: tuple
    count: int = 1
    generator_field: Generator = None
    inside: bool = True
    start_row: int = None
    start_column: int = None

    def __post_init__(self):
        self.generator_field = self.travel_in_direction()
        self.start_row = self.row
        self.start_column = self.column
        self.row += self.direction[0]
        self.column += self.direction[1]
        self.inside = inside_board(self.row, self.column)

    def travel_in_direction(self):
        while inside_board(self.row, self.column):
            yield self
            self.row += self.direction[0]
            self.column += self.direction[1]
            self.count += 1

    @property
    def single_pass(self):
        for value in self.generator_field:
            yield value
            break

    @property
    def full_coords(self):
        return self.start_row, self.start_column, self.row, self.column

    @property
    def current_coords(self):
        return self.row, self.column

    @property
    def start_coords(self):
        return self.start_row, self.start_column

    @property
    def delta_row(self):
        return self.direction[0]

    @property
    def delta_column(self):
        return self.direction[1]

    @property
    def deltas(self):
        return self.direction, (-self.delta_row, - self.delta_column)


class GameState:
    def __init__(self):
        self.board = Board()
        self.move_functions = {'p': self.get_pawn_moves, 'R': self.get_rook_moves, 'N': self.get_knight_moves,
                               'B': self.get_bishop_moves, 'Q': self.get_queen_moves, 'K': self.get_king_moves}
        self.states = State()

    def process_move(self, move):
        move.process()
        self.states.update_states(move)

    def undo_move(self):
        self.states.undo()

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
                    if possible_moves[i].piece_moved[1] != 'K':
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
        for row in self.board.board:
            for board_tile in row:
                if board_tile.color == self.states.player:
                    self.move_functions[board_tile.chess_piece](board_tile.row, board_tile.column, moves)
        return moves

    def get_pawn_moves(self, row, column, moves):
        piece_pinned, pin_direction = self.is_pinned(row, column)
        direction = -1 if self.states.white_to_move else 1

        if not piece_pinned or pin_direction in ((-direction, 0), (direction, 0)):
            self.add_pawn_forward_move(row, column, direction, moves, self.board)
        if column > 0 and (not piece_pinned or pin_direction in ((0, -1), (0, 1))):
            self.add_pawn_left_move(row, column, direction, moves)
        if column + 1 < BOARDLENGTH and (not piece_pinned or pin_direction in ((0, 1), (0, -1))):
            self.add_pawn_right_move(row, column, direction, moves)

    def add_pawn_forward_move(self, row, column, direction, moves, board):
        if board.get(row + direction, column).is_empty:
            moves.append(Move(board.get(row, column), board.get(row + direction, column), "", ""))
        self.add_pawn_double_move(row, column, direction * 2, moves, board)

    def add_pawn_double_move(self, row, column, direction, moves, board):
        starting_row_for_pawns = 6 if self.states.white_to_move else 1
        forward_by_two = row + direction
        if row == starting_row_for_pawns and self.board.get(forward_by_two, column).is_empty:
            moves.append(Move(board.get(row, column), board.get(forward_by_two, column), "", ""))

    def add_pawn_left_move(self, row, column, direction, moves):
        board = self.board
        if board.get(row + direction, column - 1).color == self.states.opponent:
            moves.append(Move(board.get(row, column), board.get(row + direction, column - 1), "", ""))
        elif (row + direction, column - 1) == self.states.enpassant_possible:
            self.enpassant_left_check(row, column, direction, moves)

    def add_pawn_right_move(self, row, column, direction, moves):
        board = self.board
        if board.get(row + direction, column + 1).color == self.states.opponent:
            moves.append(Move(board.get(row, column), board.get(row + direction, column + 1), "", ""))
        elif (row + direction, column + 1) == self.states.enpassant_possible:
            self.enpassant_right_check(row, column, direction, moves)

    def enpassant_left_check(self, row, column, direction, moves):
        king_row, king_column = self.states.king_position
        board = self.board
        blocking_piece = attacking_piece = False
        for i in range(BOARDLENGTH - 1, 0, -1):
            if any(king_column + difference in (column, column - 1, king_column) for difference in (-i, i)):
                continue
            if king_column - i >= 0 and not board.get(row, king_column - i).is_empty:
                board_square = board.get(row, king_column - i)
                attacking_piece = board_square.color == self.states.opponent and board_square.chess_piece in (
                    'R', 'Q')
                blocking_piece = board_square.color == self.states.player and not attacking_piece
            if king_column + i < BOARDLENGTH and not board.get(row, king_column + i).is_empty:
                board_square = board.get(row, king_column + i)
                attacking_piece = attacking_piece or board_square == self.states.opponent and board_square.chess_piece in (
                    'R', 'Q')
                blocking_piece = board_square.color == self.states.player and not attacking_piece

        if (not attacking_piece or blocking_piece) or king_row != row:
            moves.append(EnpassantMove(board.get(row, column), board.get(row + direction, column - 1)
                                       , "", "", board.get(row, column - 1)))

    #TODO
    def enpassant_right_check(self, row, column, direction, moves):
        king_row, king_column = self.states.king_position
        blocking_piece = attacking_piece = False
        board = self.board
        #
        #     if any(king_column + difference in (column, column + 1, king_column) for difference in (-i, i)):
        #         continue
        #     if king_column - i >= 0 and not board.get(row, king_column - i).is_empty:
        #         board_square = board.get(row, king_column - i)
        #         attacking_piece = board_square.color == self.states.opponent and board_square.chess_piece in (
        #             'R', 'Q')
        #         blocking_piece = board_square.color == self.states.player and not attacking_piece
        #     if king_column + i < BOARDLENGTH and not board.get(row, king_column + i).is_empty:
        #         attacking_piece = attacking_piece or board_square == self.states.opponent and board_square.chess_piece in (
        #             'R', 'Q')
        #         blocking_piece = board_square.color == self.states.player and not attacking_piece
        # if not attacking_piece or blocking_piece or king_row != row:
        #     moves.append(EnpassantMove(board.get(row, column), board.get(row + direction, column + 1)
        #                                , "", "", board.get(row, column + 1)))

    def get_rook_moves(self, row, column, moves):
        pinned, pin_direction = self.is_pinned(row, column)
        for direction in self.direction_list(row, column, ROOK_DIRECTIONS):
            if not pinned or pin_direction in direction.deltas:
                self.add_capturable(direction.generator_field, self.board, moves)

    def get_knight_moves(self, row, column, moves):
        pinned, pin_direction = self.is_pinned(row, column)
        if pinned: return
        for direction in self.direction_list(row, column, KNIGHT_DIRECTIONS):
            self.add_capturable(direction.single_pass, self.board, moves)

    def get_bishop_moves(self, row, column, moves):
        pinned, pin_direction = self.is_pinned(row, column)
        for direction in self.direction_list(row, column, BISHOP_DIRECTIONS):
            if not pinned or pin_direction in direction.deltas:
                self.add_capturable(direction.generator_field, self.board, moves)

    def get_queen_moves(self, row, column, moves):
        pinned, pin_direction = self.is_pinned(row, column)
        for direction in self.direction_list(row, column, ROOK_DIRECTIONS + BISHOP_DIRECTIONS):
            if not pinned or pin_direction in direction.deltas:
                self.add_capturable(direction.generator_field, self.board, moves)

    def get_king_moves(self, row, column, moves):
        for direction in self.direction_list(row, column, ROOK_DIRECTIONS + BISHOP_DIRECTIONS):
            if not direction.inside: continue
            end_row, end_column = direction.current_coords
            end_square = self.board.get(end_row, end_column)
            if end_square.color != self.states.player:
                holder = end_square.board_value
                self.states.update_king(end_row, end_column)
                end_square.board_value = '--'
                in_checked, pins, checks = self.states.checked, copy.deepcopy(self.states.pins), copy.deepcopy(
                    self.states.checks)
                self.states.check_for_pins_and_checks(self.board)
                end_square.board_value = holder
                if not self.states.checked:
                    moves.append(Move(self.board.get(row, column), self.board.get(end_row, end_column), "", ""))
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

    def get_king_side_castle_moves(self, row, column, moves):
        if self.board.get(row, column + 1).is_empty and self.board.get(row, column + 2).is_empty:
            if not self.square_under_attack(row, column + 1) and not self.square_under_attack(row, column + 2):
                moves.append(CastleMove(self.board.get(row, column), self.board.get(row, column + 2), "", "",
                                        self.board.get(row, column + 3), self.board.get(row, column + 1)))

    def get_queen_side_castle_moves(self, row, column, moves):
        board = self.board
        if board.get(row, column - 1).is_empty and board.get(row, column - 2).is_empty and board.get(row,
                                                                                                     column - 3).is_empty:
            if not self.square_under_attack(row, column - 1) and not self.square_under_attack(row, column - 2):
                moves.append(CastleMove(board.get(row, column), board.get(row, column - 2), "", "",
                                        self.board.get(row, column - 4), self.board.get(row, column - 1)))

    def square_under_attack(self, row, column):
        return self.found_enemy_piece(row, column)

    # TODO
    def found_enemy_piece(self, row, column):
        for directions in self.direction_list(row, column, ROOK_DIRECTIONS + BISHOP_DIRECTIONS):
            if self.find_capture(directions.generator_field, self.board):
                return True
        for directions in self.direction_list(row, column, KNIGHT_DIRECTIONS):
            if self.find_capture(directions.generator_field, self.board):
                return True
        return False

    def find_capture(self, generator, board):
        for coordinates in generator:
            end_tile = board.get(*coordinates.current_coords)
            if not end_tile.is_empty and end_tile.color == self.states.player:
                return False
            if end_tile.color == self.states.opponent and self.states.can_check(coordinates.count,
                                                                                coordinates.direction,
                                                                                end_tile.chess_piece):
                return True
        return False

    def add_capturable(self, generator, board, moves):
        for coordinates in generator:
            end_tile = board.get(*coordinates.current_coords)
            if not end_tile.is_empty and end_tile.color == self.states.player:
                break
            moves.append(Move(self.board.get(*coordinates.start_coords), end_tile, "", ""))
            if end_tile.capturable_by(self.states.player):
                break

    @staticmethod
    def direction_list(row, column, directions):
        return tuple(map(lambda delta: Direction(row, column, delta), directions))
