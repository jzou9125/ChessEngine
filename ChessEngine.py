# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import copy
import States
from Direction import Direction
from Move import Move, EnpassantMove, CastleMove
from Board import Board

BOARDLENGTH = 8
KNIGHT_DIRECTIONS = ((1, 2), (1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1), (-1, 2), (-1, -2))
ROOK_DIRECTIONS = ((1, 0), (0, 1), (-1, 0), (0, -1))
BISHOP_DIRECTIONS = ((1, 1), (-1, -1), (1, -1), (-1, 1))


def inside_board(row, column):
    return row in range(BOARDLENGTH) and column in range(BOARDLENGTH)


class GameState:
    def __init__(self):
        self.board = Board()
        self.move_functions = {'p': self.get_pawn_moves, 'R': self.get_rook_moves, 'N': self.get_knight_moves,
                               'B': self.get_bishop_moves, 'Q': self.get_queen_moves, 'K': self.get_king_moves}
        self.states = States.State()

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
            self.add_pawn_left_move(row, column, direction, moves, self.board)
        if column + 1 < BOARDLENGTH and (not piece_pinned or pin_direction in ((0, 1), (0, -1))):
            self.add_pawn_right_move(row, column, direction, moves, self.board)

    def add_pawn_forward_move(self, row, column, direction, moves, board):
        if board.get(row + direction, column).is_empty:
            moves.append(Move(board.get(row, column), board.get(row + direction, column), "", ""))
        self.add_pawn_double_move(row, column, direction * 2, moves, board)

    def add_pawn_double_move(self, row, column, direction, moves, board):
        starting_row_for_pawns = 6 if self.states.white_to_move else 1
        forward_by_two = row + direction
        if row == starting_row_for_pawns and self.board.get(forward_by_two, column).is_empty:
            moves.append(Move(board.get(row, column), board.get(forward_by_two, column), "", ""))

    def add_pawn_left_move(self, row, column, direction, moves, board):
        if board.get(row + direction, column - 1).color == self.states.opponent:
            moves.append(Move(board.get(row, column), board.get(row + direction, column - 1), "", ""))
        elif (row + direction, column - 1) == self.states.enpassant_possible:
            self.enpassant_left_check(row, column, direction, moves, board)

    def add_pawn_right_move(self, row, column, direction, moves, board):
        if board.get(row + direction, column + 1).color == self.states.opponent:
            moves.append(Move(board.get(row, column), board.get(row + direction, column + 1), "", ""))
        elif (row + direction, column + 1) == self.states.enpassant_possible:
            self.enpassant_right_check(row, column, direction, moves, board)

    def enpassant_left_check(self, row, column, direction, moves, board):
        king_row, king_column = self.states.king_position
        left = Direction(row, min(king_column, column - 1), (0, -1))
        right = Direction(row, max(king_column, column), (0, 1))
        left_attacking = self.find_capture(left.generator_field, board)
        right_attacking = self.find_capture(right.generator_field, board)
        if king_row != row or not left_attacking and not right_attacking:
            moves.append(EnpassantMove(board.get(row, column), board.get(row + direction, column - 1)
                                       , "", "", board.get(row, column - 1)))

    # TODO
    def enpassant_right_check(self, row, column, direction, moves, board):
        king_row, king_column = self.states.king_position
        left = Direction(row, min(king_column, column), (0, -1))
        right = Direction(row, max(king_column, column + 1), (0, 1))
        left_attacking = self.find_capture(left.generator_field, board)
        right_attacking = self.find_capture(right.generator_field, board)
        if king_row != row or not left_attacking and not right_attacking:
            moves.append(EnpassantMove(board.get(row, column), board.get(row + direction, column + 1)
                                       , "", "", board.get(row, column + 1)))

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
        for direction in self.direction_list(row, column, ROOK_DIRECTIONS+BISHOP_DIRECTIONS):
            self.verify_king_move(direction.single_pass, self.board, moves)

    def verify_king_move(self, generator, board, moves):
        for direction in generator:
            end_row, end_column = direction.current_coords
            board_tile = board.get(end_row, end_column)
            empty_or_capturable = board_tile.is_empty or board_tile.capturable_by(self.states.player)
            if empty_or_capturable and not self.square_under_attack(end_row, end_column):
                moves.append(Move(self.board.get(direction.start_row, direction.start_column), self.board.get(end_row, end_column), "", ""))

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

    def found_enemy_piece(self, row, column):
        for directions in self.direction_list(row, column, ROOK_DIRECTIONS + BISHOP_DIRECTIONS):
            if self.find_capture(directions.generator_field, self.board):
                return True
        for directions in self.direction_list(row, column, KNIGHT_DIRECTIONS):
            if self.find_capture(directions.single_pass, self.board):
                return True
        return False

    def find_capture(self, generator, board):
        for direction in generator:
            end_tile = board.get(*direction.current_coords)
            if end_tile.is_empty:
                continue
            return self.states.can_check(direction.count, direction.direction, end_tile.chess_piece) and \
                   self.states.opponent == end_tile.color
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
