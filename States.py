from dataclasses import dataclass, field
from typing import Optional, NamedTuple
from Move import Move


class CastleRights(NamedTuple):
    wks: bool = True
    bks: bool = True
    wqs: bool = True
    bqs: bool = True


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

    def update(self, move):
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

    def update_castle_rights(self, move):
        player = 'w' if len(self.castle_rights_logs) % 2 else 'b'
        dictionary = self.castle_rights._asdict()
        if move.piece_moved[1] == 'K':
            dictionary[player+'ks'] = False
            dictionary[player+'qs'] = False
        elif 'R' in move.piece_moved + move.piece_captured:
            if 7 in (move.start_column, move.end_column):
                dictionary[player+'ks'] = False
            else:
                dictionary[player+'qs'] = False

        self.castle_rights = CastleRights(*dictionary.values())
        self.castle_rights_logs.append(self.castle_rights)
