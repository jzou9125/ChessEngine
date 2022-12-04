from multiprocessing import Process, Queue
import pygame as p
import ChessEngine
import AI

BOARD_WIDTH = BOARD_HEIGHT = 512
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8
SQUARE_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}


def load_images():
    pieces = ['wp', 'wN', 'wR', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("pieces/" + piece + '.png').convert_alpha(),
                                          (SQUARE_SIZE, SQUARE_SIZE))


def main():
    p.init()
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    load_images()
    move_log_font = p.font.SysFont('Arial', 12, False, False)
    clock = p.time.Clock()
    game_state = ChessEngine.GameState()
    valid_moves = game_state.get_valid_moves()

    animate = False
    move_made = False
    player_clicks = []
    player_one = True
    player_two = True
    game_over = False
    ai_thinking = False
    move_finder_process = False
    running = True
    while running:
        is_human_turn = (game_state.states.white_to_move and player_one) or (not game_state.states.white_to_move and player_two)
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            elif e.type == p.MOUSEBUTTONDOWN:  # mouse handler
                move_made, animate = mouse_handler(game_over, is_human_turn, player_clicks, game_state, valid_moves)
            if e.type == p.KEYDOWN:
                move_made, animate, game_over = keyboard_handler(e, game_state, valid_moves, player_clicks)

        if not game_over and not is_human_turn:
            if not ai_thinking:
                ai_thinking = True
                print('thinking...')
                return_queue = Queue()
                move_finder_process = Process(target=AI.find_best_move, args=(game_state, valid_moves, return_queue))
                move_finder_process.start()

            if not move_finder_process.is_alive():
                ai_move = return_queue.get()
                if ai_move is None:
                    ai_move = AI.find_random_move(valid_moves)
                game_state.process_move(ai_move)
                move_made, animate, ai_thinking = True, True, False

        if move_made:
            if animate:
                animate_move(game_state.states.move_logs[-1], screen, game_state.board, clock)
            valid_moves = game_state.get_valid_moves()
            move_made = False

        draw_game_state(screen, game_state, valid_moves, player_clicks[0] if player_clicks else (), move_log_font)

        if game_state.states.checkmate or game_state.states.stalemate:
            game_over = True
            text = "Stalemate" if game_state.states.stalemate else "Black wins by checkmate" \
                if game_state.states.white_to_move else "White wins by checkmate"
            draw_text(screen, text)

        clock.tick(MAX_FPS)
        p.display.flip()


def mouse_handler(game_over, is_human_turn, player_clicks, game_state, valid_moves):
    move_made, animate = False, False
    if not game_over and is_human_turn:
        location = p.mouse.get_pos()
        column, row = map(transform_to_grid, location)
        if column >= 8 or player_clicks and (row, column) == player_clicks[0]:
            player_clicks = []
        else:
            if len(player_clicks) == 0 and game_state.board[row][column][0] == \
                    ('w' if game_state.states.white_to_move else 'b'):
                player_clicks.append((row, column))
            elif len(player_clicks) == 1:
                start, target = player_clicks.pop(), (row, column)
                for move in valid_moves:
                    if (move.startRow, move.startColumn) == start and (
                            move.endRow, move.endColumn) == target:
                        if move.isPromotion:
                            color = 'w' if game_state.states.white_to_move else 'b'
                            move.promotionPiece = input(
                                "choose a character to promote to 'N', 'Q', 'B', 'R'")
                            while move.promotionPiece not in game_state.moveFunctions:
                                move.promotionPiece = input(
                                    "choose a character to promote to 'N', 'Q', 'B', 'R'")
                            move.promotionPiece = color + move.promotionPiece
                        game_state.process_move(move)
                        move_made = True
                        animate = True
                else:
                    player_clicks.append((row, column))
    return move_made, animate


def keyboard_handler(e, game_state, valid_moves, player_clicks):
    move_made, animate, game_over = False, False, False
    if e.key == p.K_z:
        game_state.undo_move()
        move_made = True
        animate = False
        game_over = False
    if e.key == p.K_r:
        game_state = ChessEngine.GameState()
        valid_moves = game_state.get_valid_moves()
        player_clicks = []
        move_made = False
        animate = False
        game_over = False
    return move_made, animate, game_over

def draw_game_state(screen, game_state, valid_moves, square_selected, move_log_font):
    draw_board(screen)
    highlight_selected_square(screen, game_state, valid_moves, square_selected)
    draw_pieces(screen, game_state.board)
    draw_move_log(screen, game_state, move_log_font)


def draw_board(screen):
    global colors
    colors = [p.Color("white"), p.Color("gray")]
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            color = colors[(row + column) % 2]
            p.draw.rect(screen, color, p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


def highlight_selected_square(screen, game_state, valid_moves, square_selected):
    if square_selected != ():
        row, column = square_selected
        if game_state.board[row][column][0] == ('w' if game_state.states.white_to_move else 'b'):
            surface = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
            surface.set_alpha(100)
            surface.fill(p.Color('blue'))
            screen.blit(surface, (column * SQUARE_SIZE, row * SQUARE_SIZE))

            surface.fill(p.Color('yellow'))
            for move in valid_moves:
                if move.startRow == row and move.startColumn == column:
                    screen.blit(surface, (SQUARE_SIZE * move.endColumn, SQUARE_SIZE * move.endRow))


def draw_pieces(screen, board):
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            piece = board[row][column]
            if piece != '--':
                screen.blit(IMAGES[piece], p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


def draw_move_log(screen, game_state, move_log_font):
    move_log_rect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color('black'), move_log_rect)
    move_log = game_state.states.move_logs
    move_texts = []
    moves_per_row = 3
    for i in range(0, len(move_log), 2):
        move_string = f"{i // 2 + 1}. {str(move_log[i])} "
        if i + 1 < len(move_log):
            move_string += f"{str(move_log[i + 1])}      "
        move_texts.append(move_string)
    padding = 5
    text_y = padding
    for i in range(0, len(move_texts), moves_per_row):
        text = ""
        for j in range(moves_per_row):
            if i + j < len(move_texts):
                text += move_texts[i + j]

        text_object = move_log_font.render(text, True, p.Color('white'))
        text_location = move_log_rect.move(padding, text_y)
        screen.blit(text_object, text_location)
        text_y += text_object.get_height()


def animate_move(move, screen, board, clock):
    global colors
    change_row = move.endRow - move.startRow
    change_column = move.endColumn - move.startColumn
    frames_per_square = 10
    frame_count = (abs(change_row) + abs(change_column)) * frames_per_square
    for frame in range(frame_count + 1):
        row, column = (move.startRow + (change_row * frame / frame_count),
                       move.startColumn + change_column * frame / frame_count)
        draw_board(screen)
        draw_pieces(screen, board)
        color = colors[(move.endRow + move.endColumn) % 2]
        end_square = p.Rect(move.endColumn * SQUARE_SIZE, move.endRow * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        p.draw.rect(screen, color, end_square)
        if move.pieceCaptured != '--':
            screen.blit(IMAGES[move.pieceCaptured], end_square)

        screen.blit(IMAGES[move.pieceMoved], p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        p.display.flip()
        clock.tick(60)


def draw_text(screen, text):
    font = p.font.SysFont('Helvitca', 32, True, False)
    text_object = font.render(text, 0, p.Color('black'))
    text_location = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - text_object.get_width() / 2,
                                                                 BOARD_HEIGHT / 2 - text_object.get_height() / 2)
    screen.blit(text_object, text_location)

def transform_to_grid(coordinate):
    return coordinate // SQUARE_SIZE

if __name__ == '__main__':
    main()
