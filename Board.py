import pygame as p
import Engine

WIDTH = HEIGHT = 512
DIMENSION = 8
SQUARE_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}


def load_images():
    pieces = ['wp', 'wN', 'wR', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("pieces/" + piece + '.png').convert_alpha(),
                                          (SQUARE_SIZE, SQUARE_SIZE))


def main():
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    animate = False
    game_state = Engine.GameState()
    load_images()
    valid_moves = game_state.get_valid_moves()
    move_made = False
    player_clicks = []

    running = True
    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            elif e.type == p.MOUSEBUTTONDOWN:  # mouse handler
                location = p.mouse.get_pos()
                column, row = map(transform_to_grid, location)
                if player_clicks and (row, column) == player_clicks[0]:
                    player_clicks = []
                else:
                    if len(player_clicks) == 0 and game_state.board[row][column][0] == \
                            ('w' if game_state.whiteToMove else 'b'):
                        player_clicks.append((row, column))
                    elif len(player_clicks) == 1:
                        start, target = player_clicks.pop(), (row, column)
                        for move in valid_moves:
                            if (move.startRow, move.startColumn) == start and (move.endRow, move.endColumn) == target:
                                if move.isPromotion:
                                    color = 'w' if game_state.whiteToMove else 'b'
                                    move.promotionPiece = input("choose a character to promote to 'N', 'Q', 'B', 'R'")
                                    while move.promotionPiece not in game_state.moveFunctions:
                                        move.promotionPiece = input(
                                            "choose a character to promote to 'N', 'Q', 'B', 'R'")
                                    move.promotionPiece = color + move.promotionPiece
                                game_state.process_move(move)
                                move_made = True
                                animate = True
                        else:
                            player_clicks.append((row, column))

            if e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    game_state.undo_move()
                    move_made = True
                    animate = False
                if e.key == p.K_r:
                    game_state = Engine.GameState()
                    valid_moves = game_state.get_valid_moves()
                    player_clicks = []
                    move_made = False
                    animate = False

        if move_made:
            if animate:
                animate_move(game_state.moveLog[-1], screen, game_state.board, clock)
            valid_moves = game_state.get_valid_moves()
            move_made = False

        draw_game_state(screen, game_state, valid_moves, player_clicks[0] if player_clicks else ())

        if len(valid_moves) == 0:
            game_over = True
            if game_state.inChecked:
                if game_state.whiteToMove:
                    draw_text(screen, "Black wins by checkmate")
                else:
                    draw_text(screen, "White wins by checkmate")
            else:
                draw_text(screen, "Stalemate")

        clock.tick(MAX_FPS)
        p.display.flip()


def transform_to_grid(coordinate):
    return coordinate // SQUARE_SIZE


def draw_board(screen):
    global colors
    colors = [p.Color("white"), p.Color("gray")]
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            color = colors[(row + column) % 2]
            p.draw.rect(screen, color, p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


def draw_pieces(screen, board):
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            piece = board[row][column]
            if piece != '--':
                screen.blit(IMAGES[piece], p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


def draw_game_state(screen, game_state, valid_moves, square_selected):
    draw_board(screen)
    highlight_selected_square(screen, game_state, valid_moves, square_selected)
    draw_pieces(screen, game_state.board)


def highlight_selected_square(screen, game_state, valid_moves, square_selected):
    if square_selected != ():
        row, column = square_selected
        if game_state.board[row][column][0] == ('w' if game_state.whiteToMove else 'b'):
            surface = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
            surface.set_alpha(100)
            surface.fill(p.Color('blue'))
            screen.blit(surface, (column * SQUARE_SIZE, row * SQUARE_SIZE))

            surface.fill(p.Color('yellow'))
            for move in valid_moves:
                if move.startRow == row and move.startColumn == column:
                    screen.blit(surface, (SQUARE_SIZE * move.endColumn, SQUARE_SIZE * move.endRow))


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
    text_location = p.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH / 2 - text_object.get_width() / 2,
                                                     HEIGHT / 2 - text_object.get_height() / 2)
    screen.blit(text_object, text_location)


if __name__ == '__main__':
    main()
