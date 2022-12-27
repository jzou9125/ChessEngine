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
    white_king: tuple[int, int] = (7, 4)
    black_king: tuple[int, int] = (0, 4)


class State:
    def __init__(self):
        self.checkmate = False
        self.stalemate = False
        self.white_turn = True

    def update(self) -> None:
        self.white_turn = not self.white_turn

    def undo(self) -> None:
        self.update_mate(1, False)
        self.white_turn = not self.white_turn

    def update_mate(self, length_of_valid_moves: int, checked: bool) -> None:
        self.checkmate = length_of_valid_moves == 0 and checked
        self.stalemate = length_of_valid_moves == 0 and not checked

    @property
    def player(self) -> str:
        return 'w' if self.white_turn else 'b'

    @property
    def opponent(self) -> str:
        return 'b' if self.white_turn else 'w'


@dataclass
class StatesLogging:
    moves: list[Move] = field(default_factory=list)
    castle_rights_logs: list[CastleRights] = field(default_factory=list)
    enpassant_logs: list[tuple] = field(default_factory=list)
    kings_position: KingPosition = field(default_factory=KingPosition)

    def __post_init__(self):
        self.castle_rights_logs = [CastleRights()]
        self.enpassant_logs = [()]

    def update(self, move: Move) -> None:
        self.moves.append(move)
        if move.moved_king:
            self.update_king(move.end_row, move.end_column, move.piece_moved[0] == 'w')
        if move.piece_moved[1] == 'p' and abs(move.start_row - move.end_row) == 2:
            enpassant_possible = ((move.start_row + move.end_row) // 2, move.start_column)
        else:
            enpassant_possible = ()
        self.enpassant_logs.append(enpassant_possible)
        self.update_castle_rights(move)

    def undo(self) -> None:
        if self.moves:
            self.enpassant_logs.pop()
            self.castle_rights_logs.pop()
            self.moves.pop().undo()
            if self.moves:
                last_move = self.moves[-1]
                if last_move.moved_king:
                    self.update_king(last_move.start_row, last_move.start_column, last_move.piece_moved[0] == 'w')

    def update_castle_rights(self, move: Move) -> None:
        player = 'w' if len(self.castle_rights_logs) % 2 else 'b'
        dictionary = self.castle_rights_logs[-1]._asdict()
        if move.piece_moved[1] == 'K':
            dictionary[player + 'ks'] = False
            dictionary[player + 'qs'] = False
        elif 'R' in move.piece_moved + move.piece_captured:
            if 7 in (move.start_column, move.end_column):
                dictionary[player + 'ks'] = False
            else:
                dictionary[player + 'qs'] = False
        self.castle_rights_logs.append(CastleRights(*dictionary.values()))

    def update_king(self, row: int, column: int, player: bool) -> None:
        king = 'white_king' if player else 'black_king'
        setattr(self.kings_position, king, (row, column))

    def get_king(self, white: bool) -> tuple[int, int]:
        return self.kings_position.white_king if white else self.kings_position.black_king

    @property
    def enpassant_possible(self) -> tuple[int, int]:
        return self.enpassant_logs[-1]

    @property
    def castle_rights(self) -> CastleRights:
        return self.castle_rights_logs[-1]
