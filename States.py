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
        if move.moved_piece[1] == 'p' and abs(move.start_row - move.end_row) == 2:
            self.enpassant_possible = ((move.start_row + move.end_row) // 2, move.start_column)
        else:
            self.enpassant_possible = ()
        self.enpassant_logs.append(self.enpassant_possible)
        self.update_castle_rights(move)
        self.castle_rights_logs.append(self.castle_rights)

    def undo(self):
        self.enpassant_logs.pop()
        self.castle_rights_logs.pop()
        self.enpassant_possible = self.enpassant_logs[-1]
        self.castle_rights = self.castle_rights_logs[-1]
        return self.moves.pop()

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

