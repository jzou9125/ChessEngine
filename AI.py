import random
from Move import PromotionMove, Move
from ChessEngine import GameState
PIECE_SCORE = {"K": 0, "Q": 10, "R": 5, "B": 3, "N": 3, "p": 1}
CHECKMATE = 1000
STALEMATE = 0
DEPTH = 3


def find_random_move(validMoves: list[Move]) -> Move:
    """
        return a random move if there is no move chosen
    """
    return validMoves[random.randint(0, len(validMoves) - 1)]


def find_best_move(game_state, valid_moves, return_queue):
    global next_move
    global count
    next_move = None
    random.shuffle(valid_moves)
    find_move_nega_max_alpha_beta(game_state, valid_moves, DEPTH, -CHECKMATE, CHECKMATE,
                                  1 if game_state.states.white_turn else -1)
    return_queue.put(next_move)

def find_move_nega_max(game_state, valid_moves, depth, turn_multiplier):
    global next_move
    if depth == 0:
        return turn_multiplier * score_board(game_state)
    max_score = -CHECKMATE
    for move in valid_moves:
        if move.promotion:
            move.promotionPiece = ('b' if turn_multiplier == 1 else 'w') + random.choice(('R', 'B', 'N', 'Q'))
        game_state.process_move(move)
        next_moves = game_state.get_valid_moves()
        score = -find_move_nega_max(game_state, valid_moves, depth - 1, -turn_multiplier)
        if score > max_score:
            max_score = score
            if depth == DEPTH:
                next_move = move
        game_state.undo_move()
    return max_score


def find_move_nega_max_alpha_beta(game_state: GameState, valid_moves: list[Move], depth: int, alpha: float, beta: float, turn_multiplier: int) -> float:
    """
        finds the highest scoring move for a given gamestate and sets the global next_move to it
    """
    global next_move
    if depth == 0:
        return turn_multiplier * score_board(game_state)
    max_score = -CHECKMATE
    for move in valid_moves:
        if isinstance(move, PromotionMove):
            move.promotionPiece = ('b' if turn_multiplier == 1 else 'w') + random.choice(('R', 'B', 'N', 'Q'))
        game_state.process_move(move)
        next_moves = game_state.get_valid_moves()
        score = -find_move_nega_max_alpha_beta(game_state, next_moves, depth - 1, -beta, -alpha, -turn_multiplier)
        if score > max_score:
            max_score = score
            if depth == DEPTH:
                next_move = move
                print(next_move, score)
        game_state.undo_move()
        alpha = max(alpha, max_score)
        if alpha >= beta:
            break
    return max_score


def score_board(game_state):
    if game_state.states.checkmate:
        if game_state.states.white_turn:
            return -CHECKMATE
        else:
            return CHECKMATE
    elif game_state.states.stalemate:
        return STALEMATE

    score = 0
    for row in game_state.board.board:
        for tile in row:
            if tile.board_value != '--':
                piece_type = tile.chess_piece
                score += (PIECE_SCORE[piece_type] if tile.color[0] == 'w' else (-PIECE_SCORE[piece_type]))
    return score

