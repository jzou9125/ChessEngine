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
    count: int = 0
    generator_field: Generator = None

    def __post_init__(self):
        self.generator_field = self.travel_in_direction()

    def travel_in_direction(self):
        self.count += 1
        self.row += self.direction[0]
        self.column += self.direction[1]
        if self.row in range(BOARDLENGTH) and self.column in range(BOARDLENGTH):
            yield self.count, self.row, self.column

    @property
    def single_pass(self):
        while self.count < 1:
            yield from self.generator_field

    @property
    def change_row(self):
        return self.direction[0]

    @property
    def change_column(self):
        return self.direction[1]


@dataclass
class PinnedDirection(Direction):
    pinned: bool = False
    pin_direction: list[tuple] = field(default_factory=list)



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
            self.add_pawn_forward_move(row, column, direction, moves)
        if column > 0 and (not piece_pinned or pin_direction in ((0, -1), (0, 1))):
            self.add_pawn_left_move(row, column, direction, moves)
        if column + 1 < BOARDLENGTH and (not piece_pinned or pin_direction in ((0, 1), (0, -1))):
            self.add_pawn_right_move(row, column, direction, moves)

    def add_pawn_forward_move(self, row, column, direction, moves):
        starting_row_for_pawns = 6 if self.states.white_to_move else 1
        forward_by_two = row + direction * 2
        board = self.board
        if board.get(row + direction, column).is_empty:
            moves.append(Move(board.get(row, column), board.get(row + direction, column), "", ""))
            if row == starting_row_for_pawns and self.board.get(forward_by_two, column).is_empty:
                moves.append(Move(board.get(row, column), board.get(forward_by_two, column), "", ""))

    def add_pawn_left_move(self, row, column, direction, moves):
        board = self.board
        if board.get(row + direction, column - 1).color == self.states.opponent:
            moves.append(Move(board.get(row, column), board.get(row + direction, column - 1), "", ""))
        elif (row+direction, column - 1) == self.states.enpassant_possible:
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
                attacking_piece = attacking_piece or board_square == self.states.opponent and board_square.chess_piece in (
                    'R', 'Q')
                blocking_piece = board_square.color == self.states.player and not attacking_piece

        if (not attacking_piece or blocking_piece) or king_row != row:
            moves.append(EnpassantMove(board.get(row, column), board.get(row + direction, column - 1)
                                       , "", "", board.get(row, column - 1)))

    def enpassant_right_check(self, row, column, direction, moves):
        king_row, king_column = self.states.king_position
        blocking_piece = attacking_piece = False
        board = self.board
        for i in range(BOARDLENGTH-1, 0, -1):
            if any(king_column + difference in (column, column + 1, king_column) for difference in (-i, i)):
                continue
            if king_column - i >= 0 and not board.get(row, king_column - i).is_empty:
                board_square = board.get(row, king_column - i)
                attacking_piece = board_square.color == self.states.opponent and board_square.chess_piece in (
                    'R', 'Q')
                blocking_piece = board_square.color == self.states.player and not attacking_piece
            if king_column + i < BOARDLENGTH and not board.get(row, king_column + i).is_empty:
                attacking_piece = attacking_piece or board_square == self.states.opponent and board_square.chess_piece in (
                    'R', 'Q')
                blocking_piece = board_square.color == self.states.player and not attacking_piece
        if not attacking_piece or blocking_piece or king_row != row:
            moves.append(EnpassantMove(board.get(row, column), board.get(row + direction, column + 1)
                                       , "", "", board.get(row, column + 1)))

    def get_rook_moves(self, row, column, moves):
        pinned, pin_direction = self.is_pinned(row, column)
        # for generator in map(lambda direction: Direction(row, column, direction), ROOK_DIRECTIONS):
        for change_row, change_column in self.pinned_direction_generator(pinned, pin_direction, ROOK_DIRECTIONS):
            for end_row, end_column in self.direction_generator(row, column, change_row, change_column):
                if self.board.get(end_row, end_column).is_empty:
                    moves.append(Move(self.board.get(row, column), self.board.get(end_row, end_column), "", ""))
                elif self.board.get(end_row, end_column).capturable_by(self.states.player):
                    moves.append(Move(self.board.get(row, column), self.board.get(end_row, end_column), "", ""))
                    break
                else:
                    break

    def get_knight_moves(self, row, column, moves):
        pinned, pin_direction = self.is_pinned(row, column)
        if pinned: return
        for generator in map(lambda delta: Direction(row, column, delta), KNIGHT_DIRECTIONS):
            for _, end_row, end_column in generator.single_pass:
                end_square = self.board.get(end_row, end_column)
                if end_square.is_empty or end_square.capturable_by(self.states.player):
                    moves.append(Move(self.board.get(row, column), self.board.get(end_row, end_column), "", ""))

    def get_bishop_moves(self, row, column, moves):
        pinned, pin_direction = self.is_pinned(row, column)
        for change_row, change_column in self.pinned_direction_generator(pinned, pin_direction, BISHOP_DIRECTIONS):
            for end_row, end_column in self.direction_generator(row, column, change_row, change_column):
                if self.board.get(end_row, end_column).is_empty:
                    moves.append(Move(self.board.get(row, column), self.board.get(end_row, end_column), "", ""))
                elif self.board.get(end_row, end_column).capturable_by(self.states.player):
                    moves.append(Move(self.board.get(row, column), self.board.get(end_row, end_column), "", ""))
                    break
                else:
                    break

    def get_queen_moves(self, row, column, moves):
        pinned, pin_direction = self.is_pinned(row, column)
        for change_row, change_column in self.pinned_direction_generator(pinned, pin_direction,
                                                                         ROOK_DIRECTIONS + BISHOP_DIRECTIONS):
            for end_row, end_column in self.direction_generator(row, column, change_row, change_column):
                if self.board.get(end_row, end_column).is_empty:
                    moves.append(Move(self.board.get(row, column), self.board.get(end_row, end_column), "", ""))
                elif self.board.get(end_row, end_column).capturable_by(self.states.player):
                    moves.append(Move(self.board.get(row, column), self.board.get(end_row, end_column), "", ""))
                    break
                else:
                    break

    def get_king_moves(self, row, column, moves):
        for generator in map(lambda delta: Direction(row, column, delta), ROOK_DIRECTIONS + BISHOP_DIRECTIONS):
            for _, end_row, end_column in generator.single_pass:
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

    def square_under_attack(self, row, column):
        self.states.change_turn()
        opponent_moves = self.get_all_possible_moves()
        self.states.change_turn()
        for move in opponent_moves:
            if move.end_row == row and move.end_column == column:
                return True
        return False

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

    def pinned_direction_generator(self, pinned, pin_direction, move_directions):
        for direction in move_directions:
            if not pinned:
                yield direction
            elif pin_direction in (direction, (-direction[0], -direction[1])):
                yield direction
    def direction_generator(self, start_row, start_column, change_row, change_column):
        while start_row + change_row in range(BOARDLENGTH) and start_column + change_column in range(BOARDLENGTH):
            start_row, start_column = start_row + change_row, start_column + change_column
            yield start_row, start_column


@dataclass
class KingPosition:
    white_king: tuple = (7, 4)
    black_king: tuple = (0, 4)

class State:
    def __init__(self):
        self.logs = States.StatesLogging()
        self.checkmate = False
        self.stalemate = False
        self.white_to_move = True
        self.is_checked = False
        self.pins = []
        self.checks = []
        self.kings_position = KingPosition()

    def change_turn(self):
        self.white_to_move = not self.white_to_move

    def update_states(self, move):
        self.logs.update(move)
        if move.moved_king:
            self.update_king(move.end_row, move.end_column)
        self.change_turn()

    def undo(self):
        if not self.logs.moves:
            return
        self.update_mate(1)
        self.change_turn()
        last_move = self.logs.undo()
        if last_move.moved_king:
            self.update_king(last_move.start_row, last_move.start_column)
        return last_move

    def check_for_pins_and_checks(self, board):
        pins, checks, self.checked = [], [], False
        start_row, start_column = self.king_position
        directions = ROOK_DIRECTIONS + BISHOP_DIRECTIONS
        generators = list(map(lambda direction: Direction(start_row, start_column, direction), directions))
        for generator in generators:
            possible_pin = ()
            for tiles_away, end_row, end_column in generator.generator_field:
                end_piece = board.get(end_row, end_column)
                if end_piece.color == self.player and end_piece.chess_piece != 'K':
                    if possible_pin == ():
                        possible_pin = (end_row, end_column, generator.change_row, generator.change_column)
                    else:
                        break
                elif end_piece.color == self.opponent:
                    if self.can_check(tiles_away, generator.direction, end_piece.chess_piece):
                        if possible_pin == ():
                            self.checked = True
                            checks.append((end_row, end_column, generator.change_row, generator.change_column))
                            break
                        else:
                            pins.append(possible_pin)
                            break
                    else:
                        break
                else:
                    break

        for generator in map(lambda direction: Direction(start_row, start_column, direction), KNIGHT_DIRECTIONS):
            for _, end_row, end_column in generator.single_pass:
                end_piece = board.get(end_row, end_column)
                if end_piece.color == self.opponent and end_piece.chess_piece == 'K':
                    self.checked = True
                    checks.append((end_row, end_column, generator.change_row, generator.change_column))

        self.pins = copy.deepcopy(pins)
        self.checks = copy.deepcopy(checks)

    def can_check(self, tiles_away, direction, piece):
        return (piece == 'Q') or (tiles_away == 1 and piece == 'K') or \
            (piece == 'R' and direction in ROOK_DIRECTIONS) or \
            (piece == 'B' and direction in BISHOP_DIRECTIONS) or \
            piece == 'p' and ((not self.white_to_move and direction in ((1, -1), (1, 1))) or
                              (self.white_to_move and direction in ((-1, 1), (-1, -1))))

    def update_mate(self, length_of_valid_moves):
        self.checkmate = length_of_valid_moves == 0 and self.checked
        self.stalemate = length_of_valid_moves == 0 and not self.checked

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
        if isinstance(value, bool):
            self.is_checked = value

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
