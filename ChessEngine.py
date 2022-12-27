# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from typing import Callable, Generator

from States import State, StatesLogging
from Direction import Direction
from Move import Move, EnpassantMove, CastleMove, PromotionMove
from Board import Board

BOARDLENGTH = 8
KNIGHT_DIRECTIONS = ((1, 2), (1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1), (-1, 2), (-1, -2))
ROOK_DIRECTIONS = ((1, 0), (0, 1), (-1, 0), (0, -1))
BISHOP_DIRECTIONS = ((1, 1), (-1, -1), (1, -1), (-1, 1))


def inside_board(row, column):
    return row in range(BOARDLENGTH) and column in range(BOARDLENGTH)


class GameState:
    def __init__(self):
        self.board = Board(BOARDLENGTH)
        self.move_functions = {'p': self.get_pawn_moves, 'R': self.get_rook_moves, 'N': self.get_knight_moves,
                               'B': self.get_bishop_moves, 'Q': self.get_queen_moves, 'K': self.get_king_moves}
        self.states = State()
        self.logs = StatesLogging()
        self.pins = []

    def process_move(self, move: Move) -> None:
        move.process()
        self.logs.update(move)
        self.states.update()

    def process_ai_move(self, move: Move) -> None:
        move.starting_tile = self.board.get(*move.start_square)
        move.ending_tile = self.board.get(*move.end_square)
        move.process()
        self.logs.update(move)
        self.states.update()

    def undo_move(self) -> None:
        if self.logs.moves:
            self.logs.undo()
            self.states.undo()

    def get_valid_moves(self) -> list[Move]:
        """
            Returns a list of valid moves based on number of checks on the king
        """
        possible_moves = []
        king_row, king_column = self.logs.get_king(self.states.white_turn)
        self.find_pins(king_row, king_column)
        count, directions = self.find_number_of_attackers(king_row, king_column)
        if count == 1:
            possible_tiles = []
            self.get_attacked_tile(king_row, king_column, directions, possible_tiles)
            possible_moves = self.get_all_possible_moves()
            self.prune(possible_tiles, possible_moves)
        elif count == 2:
            self.get_king_moves(king_row, king_column, possible_moves)
        else:
            possible_moves = self.get_all_possible_moves()
            self.get_castle_moves(king_row, king_column, possible_moves)

        self.states.update_mate(len(possible_moves), count > 0)
        return possible_moves

    def find_pins(self, row: int, column: int) -> None:
        """
            find pieces that are pinned by an enemy piece that can check the king if said piece is moved
        """
        pins = []
        for direction in self.direction_list(row, column, ROOK_DIRECTIONS + BISHOP_DIRECTIONS):
            defending_piece = 0
            defending_coord = ()
            for coordinate in direction.generator_field:
                tile = self.board.get(*coordinate.current_coords)
                if tile.is_empty:
                    continue
                elif tile.color == self.states.player:
                    defending_piece += 1
                    defending_coord = [*coordinate.current_coords]
                    if defending_piece > 1:
                        break
                elif self.can_check(coordinate, direction.direction, tile.chess_piece) and defending_piece == 1:
                    pins.append(defending_coord + list(direction.direction))
                    break
                else:
                    break
        self.pins = pins.copy()

    def prune(self, possible_tiles: list[tuple[int, int]], possible_moves: list[Move]) -> None:
        """
            removes any moves that don't block the check or isn't a move that the kings deems possible
        """
        for i in range(len(possible_moves) - 1, -1, -1):
            if (possible_moves[i].end_row, possible_moves[i].end_column) not in possible_tiles and possible_moves[i].piece_moved[1] != 'K':
                possible_moves.remove(possible_moves[i])

    def get_attacked_tile(self, row: int, column: int, directions: list[tuple[int, int]], moves: list[Move]) -> None:
        """
            find tiles that are attacked when there is a check
        """
        for direction in self.direction_list(row, column, tuple(directions)):
            for iteration in direction.generator_field:
                tile = self.board.get(*iteration.current_coords)
                if not tile.is_empty and tile.color == self.states.player:
                    break
                moves.append(iteration.current_coords)

    def find_number_of_attackers(self, row: int, column: int) -> tuple[int, list[tuple[int, int]]]:
        """
            Return number of pieces that can attack the board tile at the givern row and column
        """
        count, check_directions = 0, []
        for directions in self.straight_directions(row, column):
            if self.find_capture(directions.generator_field, self.board):
                count += 1
                check_directions.append(directions.direction)
        for directions in self.direction_list(row, column, KNIGHT_DIRECTIONS):
            if self.find_capture(directions.single_pass, self.board):
                count += 1
                check_directions.append(directions.direction)
        return count, check_directions

    def is_pinned(self, row: int, column: int) -> tuple[bool, tuple[int, int]]:
        """
            Checks if the given row and column are one of the recorded pins
        """
        pinned, pin_direction = False, ()
        for pin in self.pins:
            if (pin[0], pin[1]) == (row, column):
                pinned = True
                pin_direction = pin[2], pin[3]
                self.pins.remove(pin)
        return pinned, pin_direction

    def can_check(self, tiles_away: int, direction: tuple[int, int], piece: str) -> bool:
        """
            return whether the given piece can move to the callers position
        """
        return (piece == 'Q') or (tiles_away == 1 and piece == 'K') or \
               (piece == 'R' and direction in ROOK_DIRECTIONS) or \
               (piece == 'B' and direction in BISHOP_DIRECTIONS) or \
               (tiles_away == 1 and piece == 'p' and ((not self.states.white_turn and direction in ((1, -1), (1, 1)))
                                                 or (self.states.white_turn and direction in ((-1, 1), (-1, -1)))))\
               or (tiles_away == 1 and piece == 'N' and direction in KNIGHT_DIRECTIONS)

    def get_all_possible_moves(self) -> list[Move]:
        """
            return all possible moves for the current board
        """
        moves = []
        for row in self.board.board:
            for board_tile in row:
                if board_tile.color == self.states.player:
                    self.move_functions[board_tile.chess_piece](board_tile.row, board_tile.column, moves)
        return moves

    def get_pawn_moves(self, row: int, column: int, moves: list[Move]) -> None:
        """
            get all possible pawn moves; single, double, or enpassant moves
        """
        piece_pinned, pin_direction = self.is_pinned(row, column)
        direction = -1 if self.states.white_turn else 1
        if not piece_pinned or pin_direction in ((-direction, 0), (direction, 0)):
            self.add_pawn_forward_move(row, column, direction, moves, self.board)
        if column > 0 and (not piece_pinned or pin_direction in ((0, -1), (0, 1))):
            self.add_pawn_left_move(row, column, direction, moves, self.board)
        if column + 1 < BOARDLENGTH and (not piece_pinned or pin_direction in ((0, 1), (0, -1))):
            self.add_pawn_right_move(row, column, direction, moves, self.board)

    def add_pawn_forward_move(self, row: int, column: int, direction: int, moves: list[Move], board: Board) -> None:
        """
            checks whether the pawn can promote or move one step forward
        """
        if board.get(row + direction, column).is_empty:
            if row + direction in (0, 7):
                moves.append(PromotionMove(board.get(row, column), board.get(row + direction, column), "", ""))
            else:
                moves.append(Move(board.get(row, column), board.get(row + direction, column), "", ""))
            self.add_pawn_double_move(row, column, direction * 2, moves, board)

    def add_pawn_double_move(self, row: int, column: int, direction: int, moves: list[Move], board: Board) -> None:
        """
            checks if the pawn is still in starting position and the tile at the double position is empty
        """
        starting_row_for_pawns = 6 if self.states.white_turn else 1
        forward_by_two = row + direction
        if row == starting_row_for_pawns and self.board.get(forward_by_two, column).is_empty:
            moves.append(Move(board.get(row, column), board.get(forward_by_two, column), "", ""))

    def add_pawn_left_move(self, row: int, column: int, direction: int, moves: list[Move], board: Board) -> None:
        """
            checks whether the pawn can capture to the left or enpassant
        """
        if board.get(row + direction, column - 1).color == self.states.opponent:
            if row + direction in (0, 7):
                moves.append(PromotionMove(board.get(row, column), board.get(row + direction, column - 1), "", ""))
            else:
                moves.append(Move(board.get(row, column), board.get(row + direction, column - 1), "", ""))
        elif (row + direction, column - 1) == self.logs.enpassant_possible:
            self.enpassant_left_check(row, column, direction, moves, board)

    def add_pawn_right_move(self, row: int, column: int, direction: int, moves: list[Move], board: Board) -> None:
        """
            checks whether the pawn can capture to the right or enpassant
        """
        if board.get(row + direction, column + 1).color == self.states.opponent:
            if row + direction in (0, 7):
                moves.append(PromotionMove(board.get(row, column), board.get(row + direction, column + 1), "", ""))
            else:
                moves.append(Move(board.get(row, column), board.get(row + direction, column + 1), "", ""))
        elif (row + direction, column + 1) == self.logs.enpassant_possible:
            self.enpassant_right_check(row, column, direction, moves, board)

    def enpassant_left_check(self, row: int, column: int, direction: int, moves: list[Move], board: Board) -> None:
        """
            checks that if we enpassant, we don't allow the king to be checked
        """
        king_row, king_column = self.logs.get_king(self.states.white_turn)
        left = Direction(row, min(king_column, column - 1), (0, -1), self.board)
        right = Direction(row, max(king_column, column), (0, 1), self.board)
        left_attacking = self.find_capture(left.generator_field, board)
        right_attacking = self.find_capture(right.generator_field, board)
        if king_row != row or not left_attacking and not right_attacking:
            moves.append(EnpassantMove(board.get(row, column), board.get(row + direction, column - 1),
                                       "", "", board.get(row, column - 1)))

    def enpassant_right_check(self, row: int, column: int, direction: int, moves: list[Move], board: Board) -> None:
        """
            checks that if we enpassant, we don't allow the king to be checked
        """
        king_row, king_column = self.logs.get_king(self.states.white_turn)
        left = Direction(row, min(king_column, column), (0, -1), self.board)
        right = Direction(row, max(king_column, column + 1), (0, 1), self.board)
        left_attacking = self.find_capture(left.generator_field, board)
        right_attacking = self.find_capture(right.generator_field, board)
        if king_row != row or not left_attacking and not right_attacking:
            moves.append(EnpassantMove(board.get(row, column), board.get(row + direction, column + 1),
                                       "", "", board.get(row, column + 1)))

    def get_rook_moves(self, row: int, column: int, moves: list[Move]):
        """
            add any tiles that the rook can move to into moves argument
        """
        pinned, pin_direction = self.is_pinned(row, column)
        for direction in self.direction_list(row, column, ROOK_DIRECTIONS):
            if not pinned or pin_direction in direction.deltas:
                self.add_capturable(direction.generator_field, self.board, moves)

    def get_knight_moves(self, row: int, column: int, moves: list[Move]) -> None:
        """
            add any tiles that the knight can move to into moves argument
        """
        pinned, pin_direction = self.is_pinned(row, column)
        if pinned:
            return
        for direction in self.direction_list(row, column, KNIGHT_DIRECTIONS):
            self.add_capturable(direction.single_pass, self.board, moves)

    def get_bishop_moves(self, row: int, column: int, moves: list[Move]) -> None:
        """
            add any tiles that the bishop can move to into moves argument
        """
        pinned, pin_direction = self.is_pinned(row, column)
        for direction in self.direction_list(row, column, BISHOP_DIRECTIONS):
            if not pinned or pin_direction in direction.deltas:
                self.add_capturable(direction.generator_field, self.board, moves)

    def get_queen_moves(self, row: int, column: int, moves: list[Move]) -> None:
        """
            add any tiles that the queen can move to into moves argument
        """
        pinned, pin_direction = self.is_pinned(row, column)
        for direction in self.straight_directions(row, column):
            if not pinned or pin_direction in direction.deltas:
                self.add_capturable(direction.generator_field, self.board, moves)

    def get_king_moves(self, row: int, column: int, moves: list[Move]) -> None:
        """
            add any tiles that the king can move to into moves argument
        """
        for direction in self.straight_directions(row, column):
            self.verify_king_move(direction.single_pass, self.board, moves)

    def verify_king_move(self, generator: Generator, board: Board, moves: list[Move]) -> None:
        """
            add any tiles that the king can move to into moves argument if the king would not be checked afterwards
        """
        for direction in generator:
            end_row, end_column = direction.current_coords
            board_tile = board.get(end_row, end_column)
            empty_or_capturable = board_tile.is_empty or board_tile.capturable_by(self.states.player)
            if empty_or_capturable and not self.square_under_attack(end_row, end_column):
                moves.append(Move(self.board.get(direction.start_row, direction.start_column),
                                  self.board.get(end_row, end_column), "", ""))

    def get_castle_moves(self, row: int, column: int, moves: list[Move]) -> None:
        """
            checks if king can castle if the king or rook hasn't been moved in game
        """
        if getattr(self.logs.castle_rights, self.states.player + "ks"):
            self.get_king_side_castle_moves(row, column, moves)
        if getattr(self.logs.castle_rights, self.states.player + "qs"):
            self.get_queen_side_castle_moves(row, column, moves)

    def get_king_side_castle_moves(self, row: int, column: int, moves: list[Move]) -> None:
        """
            checks if a castle on the king side is possible
        """
        if self.board.get(row, column + 1).is_empty and self.board.get(row, column + 2).is_empty:
            if not self.square_under_attack(row, column + 1) and not self.square_under_attack(row, column + 2):
                moves.append(CastleMove(self.board.get(row, column), self.board.get(row, column + 2), "", "",
                                        self.board.get(row, column + 3), self.board.get(row, column + 1)))

    def get_queen_side_castle_moves(self, row: int, column: int, moves: list[Move]) -> None:
        """
            checks if a castle on the queen side is possible
        """
        board = self.board
        if board.get(row, column - 1).is_empty and board.get(row, column - 2).is_empty \
                and board.get(row, column - 3).is_empty:
            if not self.square_under_attack(row, column - 1) and not self.square_under_attack(row, column - 2):
                moves.append(CastleMove(board.get(row, column), board.get(row, column - 2), "", "",
                                        self.board.get(row, column - 4), self.board.get(row, column - 1)))

    def square_under_attack(self, row: int, column: int) -> bool:
        """
        Returns True if the square under attack is in the given position.
        """
        for directions in self.direction_list(row, column, ROOK_DIRECTIONS + BISHOP_DIRECTIONS):
            if self.find_capture(directions.generator_field, self.board):
                return True
        for directions in self.direction_list(row, column, KNIGHT_DIRECTIONS):
            if self.find_capture(directions.single_pass, self.board):
                return True
        return False

    def find_capture(self, generator: Generator, board: Board) -> bool:
        """
            returns whether there is a piece that can check based on direction
        """
        for direction in generator:
            end_tile = board.get(*direction.current_coords)
            if end_tile.is_empty:
                continue
            return self.can_check(direction.count, direction.direction, end_tile.chess_piece) \
                   and self.states.opponent == end_tile.color
        return False

    def add_capturable(self, generator: Generator, board: Board, moves: list[Move]) -> None:
        """
            adds available tiles that can be captured into the moves argument
        """
        for coordinates in generator:
            end_tile = board.get(*coordinates.current_coords)
            if not end_tile.is_empty and end_tile.color == self.states.player:
                break
            moves.append(Move(self.board.get(*coordinates.start_coords), end_tile, "", ""))
            if end_tile.capturable_by(self.states.player):
                break

    def direction_list(self, row: int, column: int, directions: tuple[tuple[int, int], ...]) -> tuple[Direction, ...]:
        """
            returns a tuple of the class Direction instantiations
        """
        return tuple(map(lambda delta: Direction(row, column, delta, board=self.board), directions))

    def straight_directions(self, row: int, column: int) -> tuple[Direction, ...]:
        """
            a helper function that returns both rook and bishop direction
        """
        return self.direction_list(row, column, ROOK_DIRECTIONS + BISHOP_DIRECTIONS)

