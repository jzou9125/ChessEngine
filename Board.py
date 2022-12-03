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
                        move = Engine.Move(player_clicks.pop(0), (row, column), game_state.board)
                        print(move.get_chess_notation())
                        if move in valid_moves:
                            if move.isPromotion:
                                color = 'w' if game_state.whiteToMove else 'b'
                                move.promotionPiece = input("choose a character to promote to 'N', 'Q', 'B', 'R'")
                                while move.promotionPiece not in game_state.moveFunctions:
                                    move.promotionPiece = input("choose a character to promote to 'N', 'Q', 'B', 'R'")
                                move.promotionPiece = color + move.promotionPiece
                            game_state.process_move(move)
                            move_made = True
                        else:
                            player_clicks.append((row, column))

            if e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    game_state.undo_move()
                    move_made = True

        if move_made:
            valid_moves = game_state.get_valid_moves()
            move_made = False

        draw_game_state(screen, game_state)
        clock.tick(MAX_FPS)
        p.display.flip()


def transform_to_grid(coordinate):
    return coordinate // SQUARE_SIZE


def draw_board(screen):
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


def draw_game_state(screen, gs):
    draw_board(screen)
    draw_pieces(screen, gs.board)


def draw_possible_moves(screen, gs):
    pass


if __name__ == '__main__':
    main()
