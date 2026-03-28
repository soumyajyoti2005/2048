import pygame as pg
import random as rd
import math
import asyncio

# --------------- initialize pygame ---------------
pg.init() 

# --------------- setting up pygame display --------------
FPS = 60

WIDTH,HEIGHT = 800,800
ROWS = 4
COLS = 4

RECT_HEIGHT = HEIGHT//ROWS
RECT_WIDTH  = WIDTH//COLS
BORDER_RADIUS = 12


OUTLINE_THICKNESS = 5

FONT_COLOR = (64, 0, 128)
OUTLINE_COLOR     = (58, 32, 64)     # #3a2040
BACKGROUND_COLOR  = (37, 21, 37)     # #251525
VACANT_TILE_COLOR = (51, 30, 51)     # #331e33

FONT = pg.font.SysFont("comicsans",60,bold = True)
MOVE_VEL = 20
PAD = 10
OUTER_PAD = 10 

WINDOW = pg.display.set_mode((WIDTH + OUTER_PAD * 2, HEIGHT + OUTER_PAD * 2))
pg.display.set_caption("2048")

# ------------------- Tiles Class ------------------------
class Tile:
    COLORS = {
    2:    (122, 48, 96),    # #7a3060  — soft muted pink
    4:    (154, 56, 112),   # #9a3870  — dusty rose
    8:    (184, 66, 130),   # #b84282  — medium pink
    16:   (205, 82, 147),   # #cd5293  — warm pink
    32:   (224, 96, 160),   # #e060a0  — bright pink
    64:   (220, 60, 120),   # #dc3c78  — hot pink
    128:  (200, 40, 100),   # #c82864  — deep rose
    256:  (180, 20, 80),    # #b41450  — rich magenta
    512:  (160, 10, 60),    # #a00a3c  — deep magenta
    1024: (130, 5, 45),     # #82052d  — dark crimson
    2048: (255, 220, 240),  # #ffdcf0  — bright white-pink (special!)
    }

    def __init__(self,value,row,col):
        self.value = value
        self.row = row
        self.col = col
        self.x = col * RECT_WIDTH
        self.y = row * RECT_HEIGHT

    def get_color(self):
        color_key = self.value
        color = self.COLORS[color_key]
        return color

    def draw(self, window):
        color = self.get_color()
        pg.draw.rect(window, color, (
            OUTER_PAD + self.x + PAD,
            OUTER_PAD + self.y + PAD,
            RECT_WIDTH - PAD * 2,
            RECT_HEIGHT - PAD * 2
        ), border_radius=BORDER_RADIUS)

        text = FONT.render(str(self.value), 1, FONT_COLOR)
        window.blit(
            text,
            (OUTER_PAD + self.x + (RECT_WIDTH / 2 - text.get_width() / 2),
            OUTER_PAD + self.y + (RECT_HEIGHT / 2 - text.get_height() / 2))
        )

    def set_pos(self,ceil = False):
        if ceil:
            self.row = math.ceil(self.y/RECT_HEIGHT)
            self.col = math.ceil(self.x/RECT_WIDTH)

        else :
            self.row = math.floor(self.y/RECT_HEIGHT)
            self.col = math.floor(self.x/RECT_WIDTH)

    def move(self,delta):
        self.x += delta[0]
        self.y += delta[1]

# ------------------- Drawing Grid -------------------------
def draw_grid(window):
    for row in range(ROWS):
        y = OUTER_PAD + row * RECT_HEIGHT
        for col in range(COLS):
            x = OUTER_PAD + col * RECT_WIDTH
            pg.draw.rect(window, VACANT_TILE_COLOR, (
                x + PAD,
                y + PAD,
                RECT_WIDTH - PAD * 2,
                RECT_HEIGHT - PAD * 2
            ), border_radius=BORDER_RADIUS)

    pg.draw.rect(window, OUTLINE_COLOR, (0, 0, WIDTH + OUTER_PAD * 2, HEIGHT + OUTER_PAD * 2), OUTLINE_THICKNESS + 2, BORDER_RADIUS)
    

# ------------------- Drawing Screen-------------------------

def draw(window,tiles):
    window.fill(BACKGROUND_COLOR)

    draw_grid(window)

    for tile in tiles.values():
        tile.draw(window)

    pg.display.update()


# ------------------- Handling Movement of Tiles ---------------
def move_tiles(window, tiles, clock, direction):
    updated = True
    blocks = set()

    if direction == "left":
        sort_func = lambda x: x.col
        reverse = False
        delta = (-MOVE_VEL, 0)
        boundary_check = lambda tile: tile.col == 0
        get_next_tile = lambda tile: tiles.get(f"{tile.row}{tile.col - 1}")
        merge_check = lambda tile, next_tile: tile.x > next_tile.x + MOVE_VEL
        move_check = lambda tile, next_tile: tile.x > next_tile.x + RECT_WIDTH + MOVE_VEL
        ceil = True

    elif direction == "right":
        sort_func = lambda x: x.col
        reverse = True
        delta = (MOVE_VEL, 0)
        boundary_check = lambda tile: tile.col == COLS - 1
        get_next_tile = lambda tile: tiles.get(f"{tile.row}{tile.col + 1}")
        merge_check = lambda tile, next_tile: tile.x < next_tile.x - MOVE_VEL
        move_check = lambda tile, next_tile: tile.x + RECT_WIDTH + MOVE_VEL < next_tile.x
        ceil = False

    elif direction == "up":
        sort_func = lambda x: x.row
        reverse = False
        delta = (0, -MOVE_VEL)
        boundary_check = lambda tile: tile.row == 0
        get_next_tile = lambda tile: tiles.get(f"{tile.row - 1}{tile.col}")
        merge_check = lambda tile, next_tile: tile.y > next_tile.y + MOVE_VEL
        move_check = lambda tile, next_tile: tile.y > next_tile.y + RECT_HEIGHT + MOVE_VEL
        ceil = True

    elif direction == "down":
        sort_func = lambda x: x.row
        reverse = True
        delta = (0, MOVE_VEL)
        boundary_check = lambda tile: tile.row == ROWS - 1
        get_next_tile = lambda tile: tiles.get(f"{tile.row + 1}{tile.col}")
        merge_check = lambda tile, next_tile: tile.y < next_tile.y - MOVE_VEL
        move_check = lambda tile, next_tile: tile.y + RECT_HEIGHT + MOVE_VEL < next_tile.y
        ceil = False

    while updated:
        clock.tick(FPS)
        updated = False
        sorted_tiles = sorted(tiles.values(), key=sort_func, reverse=reverse)

        for i, tile in enumerate(sorted_tiles):
            if boundary_check(tile):
                continue

            next_tile = get_next_tile(tile)
            if not next_tile:
                tile.move(delta)

            elif tile.value == next_tile.value and tile not in blocks and next_tile not in blocks:
                if merge_check(tile, next_tile):
                    tile.move(delta)
                else:
                    next_tile.value *= 2
                    sorted_tiles.pop(i)
                    blocks.add(next_tile)

            elif move_check(tile, next_tile):
                tile.move(delta)

            else:
                continue

            tile.set_pos(ceil)
            updated = True

        update_tiles(window, tiles, sorted_tiles)

    return end_move(tiles)

def end_move(tiles):
    if len(tiles) == 16 and not can_merge(tiles):
        return "lost"

    if len(tiles) < 16:
        row, col = get_random_pos(tiles)
        tiles[f"{row}{col}"] = Tile(rd.choice([2, 4]), row, col)

    return "continue"


def update_tiles(window,tiles,sorted_tiles):
    tiles.clear()

    for tile in sorted_tiles:
        tiles[f"{tile.row}{tile.col}"] = tile

    draw(window,tiles)
  
# ------------------- Generate Tiles Randomly -----------------
def get_random_pos(tiles):
    
    r=None
    c=None

    while True :
        r = rd.randint(0,3)
        c = rd.randint(0,3)

        if f"{r}{c}" not in tiles :
            break

    return r,c

def generate_tiles():
    tiles = {}

    for _ in range(2):
        row,col = get_random_pos(tiles)
        tiles[f"{row}{col}"] = Tile(2,row,col)

    return tiles

# ------------------- Game Over ------------------------
def can_merge(tiles):
    for tile in tiles.values():
        right = tiles.get(f"{tile.row}{tile.col + 1}")
        if right and tile.value == right.value:
            return True
        down = tiles.get(f"{tile.row + 1}{tile.col}")
        if down and tile.value == down.value:
            return True
    return False

def draw_game_over(window):
    overlay = pg.Surface((WIDTH + OUTER_PAD * 2, HEIGHT + OUTER_PAD * 2), pg.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    window.blit(overlay, (0, 0))

    font_big = pg.font.SysFont("comicsans", 80, bold=True)
    text = font_big.render("GAME OVER!", 1, (255, 220, 240))
    window.blit(text, (
        (WIDTH + OUTER_PAD * 2) / 2 - text.get_width() / 2,
        (HEIGHT + OUTER_PAD * 2) / 2 - text.get_height() / 2
    ))

    font_small = pg.font.SysFont("comicsans", 35, bold=True)
    sub = font_small.render("Press R to Restart", 1, (255, 220, 240))
    window.blit(sub, (
        (WIDTH + OUTER_PAD * 2) / 2 - sub.get_width() / 2,
        (HEIGHT + OUTER_PAD * 2) / 2 + text.get_height() / 2 + 10
    ))

    pg.display.update()

# ------------------- Main Loop Function ----------------
async def main(window):
    clock = pg.time.Clock()
    run = True
    tiles = generate_tiles()
    swipe_start = None
    SWIPE_MIN = 30
    game_over = False

    while run:
        clock.tick(FPS)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                run = False
                break

            # restart
            if event.type == pg.KEYDOWN and event.key == pg.K_r:
                tiles = generate_tiles()
                game_over = False

            if game_over:
                continue

            result = None

            if event.type == pg.KEYDOWN:
                if event.key == pg.K_LEFT:
                    result = move_tiles(window, tiles, clock, "left")
                if event.key == pg.K_RIGHT:
                    result = move_tiles(window, tiles, clock, "right")
                if event.key == pg.K_UP:
                    result = move_tiles(window, tiles, clock, "up")
                if event.key == pg.K_DOWN:
                    result = move_tiles(window, tiles, clock, "down")

            if event.type == pg.MOUSEBUTTONDOWN:
                swipe_start = event.pos

            if event.type == pg.MOUSEBUTTONUP and swipe_start:
                dx = event.pos[0] - swipe_start[0]
                dy = event.pos[1] - swipe_start[1]
                if max(abs(dx), abs(dy)) > SWIPE_MIN:
                    if abs(dx) > abs(dy):
                        result = move_tiles(window, tiles, clock, "right" if dx > 0 else "left")
                    else:
                        result = move_tiles(window, tiles, clock, "down" if dy > 0 else "up")
                swipe_start = None

            if result == "lost":
                game_over = True

        draw(WINDOW, tiles)

        if game_over:
            draw_game_over(WINDOW)

        await asyncio.sleep(0)

    pg.quit()

if __name__ == "__main__":
     asyncio.run(main(WINDOW))

