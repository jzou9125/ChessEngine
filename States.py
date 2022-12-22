import copy
from dataclasses import dataclass, field
from typing import NamedTuple
from Move import Move

KNIGHT_DIRECTIONS = ((1, 2), (1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1), (-1, 2), (-1, -2))
ROOK_DIRECTIONS = ((1, 0), (0, 1), (-1, 0), (0, -1))
BISHOP_DIRECTIONS = ((1, 1), (-1, -1), (1, -1), (-1, 1))


class CastleRights(NamedTuple):
    wks: bool = True
    bks: bool = True
    wqs: bool = True
    bqs: bool = True


@dataclass
class KingPosition:
    white_king: tuple = (7, 4)
    black_king: tuple = (0, 4)


class State:
    def __init__(self):
        self.logs = StatesLogging()
        self.checkmate = False
        self.stalemate = False
        self.white_to_move = True
        self.kings_position = KingPosition()

    def change_turn(self):
        self.white_to_move = not self.white_to_move

    def update_states(self, move: Move):
        self.logs.update(move)
        if move.moved_king:
            self.update_king(move.end_row, move.end_column)
        self.change_turn()

    def undo(self):
        if not self.logs.moves:
            return
        self.update_mate(1, False)
        self.change_turn()
        last_move = self.logs.undo()
        if last_move.moved_king:
            self.update_king(last_move.start_row, last_move.start_column)
        return last_move

    def update_mate(self, length_of_valid_moves: int, checked: bool):
        self.checkmate = length_of_valid_moves == 0 and checked
        self.stalemate = length_of_valid_moves == 0 and not checked

    def update_king(self, row: int, column: int):
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
    def player(self):
        return 'w' if self.white_to_move else 'b'

    @property
    def opponent(self):
        return 'b' if self.white_to_move else 'w'

    @property
    def king_position(self):
        king = 'white_king' if self.white_to_move else 'black_king'
        return getattr(self.kings_position, king)


@dataclass
class StatesLogging:
    castle_rights: CastleRights = CastleRights()
    enpassant_possible: tuple = ()
    moves: list[Move] = field(default_factory=list)
    castle_rights_logs: list[CastleRights] = field(default_factory=list)
    enpassant_logs: list[tuple] = field(default_factory=list)

    def __post_init__(self):
        self.castle_rights_logs = [self.castle_rights]
        self.enpassant_logs = [self.enpassant_possible]

    def update(self, move: Move):
        self.moves.append(move)
        if move.piece_moved[1] == 'p' and abs(move.start_row - move.end_row) == 2:
            self.enpassant_possible = ((move.start_row + move.end_row) // 2, move.start_column)
        else:
            self.enpassant_possible = ()
        self.enpassant_logs.append(self.enpassant_possible)
        self.update_castle_rights(move)

    def undo(self):
        self.enpassant_logs.pop()
        self.castle_rights_logs.pop()
        self.enpassant_possible = self.enpassant_logs[-1]
        self.castle_rights = self.castle_rights_logs[-1]
        self.moves[-1].undo()
        return self.moves.pop()

    def update_castle_rights(self, move: Move):
        player = 'w' if len(self.castle_rights_logs) % 2 else 'b'
        dictionary = self.castle_rights._asdict()
        if move.piece_moved[1] == 'K':
            dictionary[player + 'ks'] = False
            dictionary[player + 'qs'] = False
        elif 'R' in move.piece_moved + move.piece_captured:
            if 7 in (move.start_column, move.end_column):
                dictionary[player + 'ks'] = False
            else:
                dictionary[player + 'qs'] = False

        self.castle_rights = CastleRights(*dictionary.values())
        self.castle_rights_logs.append(self.castle_rights)
