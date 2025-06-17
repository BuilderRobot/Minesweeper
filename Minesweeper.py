#!/usr/bin/env python3

import pygame
import sys
import numpy as np
import random
import json
import os

pygame.init()

sizes = [(10, 8), (18, 14), (24, 20)]

# get screen resolution and set tile size accordingly (large difficulty fits nicely)
resolution_info = pygame.display.Info()
TILE_SIZE = int(resolution_info.current_h / (sizes[2][0] + 4))

difficulty_num = 0

# RGB tile colors
light_grass = (90, 158, 25)
dark_grass = (75, 138, 14)
light_tile = (207, 165, 81)
dark_tile = (184, 143, 61)
water = (0, 129, 138)
UI = (41, 74, 13)

BOARD_SIZE = sizes[difficulty_num]

BOARD_WIDTH = BOARD_SIZE[0]
BOARD_HEIGHT = BOARD_SIZE[1]
# board = np.array([]) #empty
# board = np.array([1, 2, 3, 4])
board = np.empty((BOARD_WIDTH, BOARD_HEIGHT), dtype=object)
num_flags = 0
num_bombs = 0

WINDOW_WIDTH = TILE_SIZE * BOARD_WIDTH
WINDOW_HEIGHT = TILE_SIZE * BOARD_HEIGHT
UI_height = TILE_SIZE * 2
window_size = WINDOW_WIDTH, WINDOW_HEIGHT + UI_height

game_lost = False
game_won = False
first_click = True
last_xy_clicked = (-1, -1)

difficulty_names = ["easy", "medium", "hard"]
best_times_file = "best_times.txt"


# load current high score or create new file with -1
def load_high_scores():
    global difficulty_names
    global best_times_file

    # If the file doesn’t exist, create with -1s
    if not os.path.exists(best_times_file):
        initial = { "easy": -1,
                    "medium": -1,
                    "hard": -1
                    }
        with open(best_times_file, "w") as f:
            json.dump(initial, f)
        return initial

    with open(best_times_file, "r") as f:
        return json.load(f)


# Save a new high score
def save_high_score(score):
    global difficulty_names
    global difficulty_num
    scores = load_high_scores()
    difficulty_name = difficulty_names[difficulty_num]
    # Only overwrite if the new score is higher
    if scores.get(difficulty_name, 0) == -1 or score < scores.get(difficulty_name, 0):
        scores[difficulty_name] = score
        best_times[difficulty_names[difficulty_num]] = score
        with open(best_times_file, "w") as f:
            json.dump(scores, f)


def create_window(difficulty):
    global BOARD_SIZE
    global BOARD_WIDTH
    global BOARD_HEIGHT
    global WINDOW_WIDTH
    global WINDOW_HEIGHT
    global window_size
    global UI_height
    global difficulty_num
    global difficulty_sprite
    global screen

    BOARD_SIZE = sizes[difficulty]
    BOARD_WIDTH = BOARD_SIZE[0]
    BOARD_HEIGHT = BOARD_SIZE[1]
    WINDOW_WIDTH = TILE_SIZE * BOARD_WIDTH
    WINDOW_HEIGHT = TILE_SIZE * BOARD_HEIGHT
    window_size = WINDOW_WIDTH, WINDOW_HEIGHT + UI_height
    UI_height = TILE_SIZE * 2
    difficulty_num = difficulty
    difficulty_sprite = difficulties[difficulty_num]
    screen = pygame.display.set_mode(window_size)


def draw_sprites():
    for i in range(BOARD_WIDTH):
        for j in range(BOARD_HEIGHT):
            current = board[i][j]
            tile = current.tile
            count = current.count
            sprite_pos = (tile.x, tile.y)

            if game_won:
                if current.is_bomb:
                    screen.fill(light_grass, rect=tile)
                else:
                    screen.fill(water, rect=tile)
                continue

            if (i + j) % 2 == 0:  # make even tiles light
                if current.revealed:
                    screen.fill(light_tile, rect=tile)
                    if count > 0:
                        screen.blit(numbers[count], sprite_pos)
                else:
                    screen.fill(light_grass, rect=tile)
            else:  # make odd tiles dark
                if current.revealed:
                    screen.fill(dark_tile, rect=tile)
                    if count > 0:
                        screen.blit(numbers[count], sprite_pos)
                else:
                    screen.fill(dark_grass, rect=tile)

            if game_lost and current.is_bomb:
                screen.blit(bomb_sprite, sprite_pos)
                continue  # don't draw flags and bombs

            if current.flagged:
                screen.blit(flag_sprite, sprite_pos)


def draw_UI():
    global game_won
    global win_time
    global best_times
    global num_bombs
    global num_flags
    UI_rect = pygame.Rect((0, 0), (WINDOW_WIDTH, 2 * TILE_SIZE))
    screen.fill(UI, rect=UI_rect)

    redo_pos = (WINDOW_WIDTH - int(TILE_SIZE * 1.5), int(TILE_SIZE * 0.5))
    screen.blit(redo_sprite, redo_pos)

    difficulty_pos = (int(TILE_SIZE * 0.5), int(TILE_SIZE * 0.5))
    screen.blit(difficulty_sprite, difficulty_pos)

    flag_pos = (WINDOW_WIDTH / 2 - TILE_SIZE, int(TILE_SIZE * 0.5))
    screen.blit(flag_sprite, flag_pos)
    draw_text(str(num_bombs - num_flags), int(TILE_SIZE / 3), int(TILE_SIZE * 0.75))

    speaker_pos = (WINDOW_WIDTH - TILE_SIZE * 3, int(TILE_SIZE * 0.5))
    if sound_on:
        screen.blit(soundon_sprite, speaker_pos)
    else:
        screen.blit(soundoff_sprite, speaker_pos)

    if game_won:
        draw_text("You Win!", 0, WINDOW_HEIGHT / 2)
        draw_text("Time: " + str(win_time / 1000) + " s", 0, WINDOW_HEIGHT / 2 + TILE_SIZE)
        draw_text("Best: " + str(best_times[difficulty_names[difficulty_num]] / 1000) + " s", 0, WINDOW_HEIGHT / 2 + TILE_SIZE * 2)


def click_UI(screenx, screeny):
    global difficulty_num
    global sound_on
    redo_pos = (WINDOW_WIDTH - int(TILE_SIZE * 1.5), int(TILE_SIZE * 0.5))
    difficulty_pos = (int(TILE_SIZE * 0.5), int(TILE_SIZE * 0.5))
    speaker_pos = (WINDOW_WIDTH - TILE_SIZE * 3, int(TILE_SIZE * 0.5))
    if (redo_pos[0] < screenx < redo_pos[0] + TILE_SIZE
            and redo_pos[1] < screeny < redo_pos[1] + TILE_SIZE):
        start_game()
    elif (difficulty_pos[0] < screenx < difficulty_pos[0] + (4 * TILE_SIZE)
          and difficulty_pos[1] < screeny < difficulty_pos[1] + TILE_SIZE):
        create_window((difficulty_num + 1) % 3)

        if sound_on:
            womps[difficulty_num].play()

        start_game()
    elif (speaker_pos[0] < screenx < speaker_pos[0] + TILE_SIZE
          and speaker_pos[1] < screeny < speaker_pos[1] + TILE_SIZE):
        sound_on = not sound_on


def click_tile(screenx, screeny, was_double_click):
    global num_bombs
    global last_xy_clicked
    tilex = int(screenx / TILE_SIZE)
    tiley = int((screeny - UI_height) / TILE_SIZE)
    if board[tilex][tiley].flagged:  # dont reveal flagged tiles
        last_xy_clicked = (tilex, tiley)
        return

    board[tilex][tiley].reveal()

    if was_double_click and last_xy_clicked == (tilex, tiley):
        surrounding = board[tilex][tiley].get_surrounding()
        for tile in surrounding:
            if not tile.flagged:
                tile.reveal()

    last_xy_clicked = (tilex, tiley)  # update double click variable

    if num_flags == num_bombs:
        check_win()

    # sounds
    if sound_on and board[tilex][tiley].is_bomb:
        bomb_sound.play()
    elif sound_on:
        shovel_sound.play()


def flag_tile(screenx, screeny):
    global num_flags  # use the global for this function
    global num_bombs

    tilex = int(screenx / TILE_SIZE)
    tiley = int((screeny - UI_height) / TILE_SIZE)

    if board[tilex][tiley].revealed:
        return

    if board[tilex][tiley].flagged:
        board[tilex][tiley].toggle_flag()
    else:  # not already flagged
        if num_flags == num_bombs:  # can't place more flags than bombs
            return
        board[tilex][tiley].toggle_flag()
        if sound_on:
            flag_sound.play()
    if num_flags == num_bombs:
        check_win()


def check_win():
    global game_won
    global num_bombs
    global win_time
    global start_time
    global best_times
    global difficulty_num
    correct = 0
    for tile in board.flat:
        if tile.flagged and tile.is_bomb:
            correct += 1
        elif not tile.revealed:
            return

    if correct == num_bombs:
        game_won = True
        if sound_on:
            win_sound.play()
        # track time to win
        win_time = pygame.time.get_ticks() - start_time
        save_high_score(win_time)


class Tile:
    # constructor
    def __init__(self, x, y):
        global UI_height
        self.x = x
        self.y = y
        self.count = 0
        self.is_bomb = False
        self.flagged = False
        self.revealed = False
        self.tile = pygame.Rect((x * TILE_SIZE, (y * TILE_SIZE) + UI_height), (TILE_SIZE, TILE_SIZE))

    def toggle_flag(self):
        global num_flags
        self.flagged = not self.flagged
        if self.flagged:
            num_flags += 1
        else:
            num_flags -= 1

    def make_bomb(self):
        self.is_bomb = True

    def get_surrounding(self):
        x = self.x
        y = self.y
        surrounding = []
        if x - 1 >= 0 and y - 1 >= 0:
            surrounding.append(board[x - 1][y - 1])
        if y - 1 >= 0:
            surrounding.append(board[x][y - 1])
        if x + 1 < BOARD_WIDTH and y - 1 >= 0:
            surrounding.append(board[x + 1][y - 1])
        if x + 1 < BOARD_WIDTH:
            surrounding.append(board[x + 1][y])
        if x + 1 < BOARD_WIDTH and y + 1 < BOARD_HEIGHT:
            surrounding.append(board[x + 1][y + 1])
        if y + 1 < BOARD_HEIGHT:
            surrounding.append(board[x][y + 1])
        if x - 1 >= 0 and y + 1 < BOARD_HEIGHT:
            surrounding.append(board[x - 1][y + 1])
        if x - 1 >= 0:
            surrounding.append(board[x - 1][y])
        return surrounding

    def reveal(self):
        global num_flags
        global game_lost
        global first_click
        if self.revealed:
            return

        self.revealed = True

        if self.flagged:
            self.toggle_flag()

        if self.is_bomb:
            if first_click:  # first click protection
                self.is_bomb = False
                self.count -= 1
                for tile in self.get_surrounding():
                    tile.count -= 1
                randx = random.randint(0, BOARD_WIDTH - 1)  # inclusive on both ends
                randy = random.randint(0, BOARD_HEIGHT - 1)

                while board[randx][randy].is_bomb:
                    randx = random.randint(0, BOARD_WIDTH - 1)  # inclusive on both ends
                    randy = random.randint(0, BOARD_HEIGHT - 1)
                board[randx][randy].is_bomb = True
                for tile in board[randx][randy].get_surrounding():
                    tile.count += 1
                # print(str(randx) + ", " + str(randy) + " is now a bomb")
                first_click = False
            else:
                game_lost = True
                self.revealed = False

        if self.count == 0:
            for tile in self.get_surrounding():
                tile.reveal()
        first_click = False


def create_bombs():
    # choose bomb number
    global num_bombs
    if BOARD_SIZE == sizes[0]:
        num_bombs = 10
    elif BOARD_SIZE == sizes[1]:
        num_bombs = 32
    else:
        num_bombs = 60

    i = 0
    while i < num_bombs:
        randx = random.randint(0, BOARD_WIDTH - 1)  # inclusive on both ends
        randy = random.randint(0, BOARD_HEIGHT - 1)
        chosen_tile = board[randx][randy]
        if chosen_tile.is_bomb:  # skip if already a bomb
            continue
        else:
            chosen_tile.make_bomb()
            chosen_tile.count += 1
            surrounding = chosen_tile.get_surrounding()
            for tile in surrounding:
                tile.count += 1
            i += 1


def draw_text(text, x, y):
    text_color = (255, 255, 255)
    font = pygame.font.SysFont("", TILE_SIZE)
    image = font.render(text, True, text_color)
    x += WINDOW_WIDTH / 2 - image.get_width() / 2
    screen.blit(image, (x, y))


# create screen
screen = pygame.display.set_mode(window_size)
pygame.display.set_caption("Minesweeper")

# must load sprites after creating screen
# initialize number sprites
numbers = np.empty(9, dtype=object)
numbers[1] = pygame.image.load("Sprites/one.png").convert_alpha()
numbers[2] = pygame.image.load("Sprites/two.png").convert_alpha()
numbers[3] = pygame.image.load("Sprites/three.png").convert_alpha()
numbers[4] = pygame.image.load("Sprites/four.png").convert_alpha()
numbers[5] = pygame.image.load("Sprites/five.png").convert_alpha()
numbers[6] = pygame.image.load("Sprites/six.png").convert_alpha()
numbers[7] = pygame.image.load("Sprites/seven.png").convert_alpha()
numbers[8] = pygame.image.load("Sprites/eight.png").convert_alpha()
for i in range(1, len(numbers)):
    numbers[i] = pygame.transform.scale(numbers[i], (TILE_SIZE, TILE_SIZE))

# UI sprites
difficulties = np.empty(3, dtype=object)
difficulties[0] = pygame.image.load("Sprites/easy.png").convert_alpha()
difficulties[1] = pygame.image.load("Sprites/medium.png").convert_alpha()
difficulties[2] = pygame.image.load("Sprites/hard.png").convert_alpha()
for i in range(len(difficulties)):
    difficulties[i] = pygame.transform.scale(difficulties[i], (TILE_SIZE * 4, TILE_SIZE))
difficulty_sprite = difficulties[0]

redo_sprite = pygame.image.load("Sprites/redo.png")
redo_sprite = pygame.transform.scale(redo_sprite, (TILE_SIZE, TILE_SIZE))

soundon_sprite = pygame.image.load("Sprites/soundon.png")
soundon_sprite = pygame.transform.scale(soundon_sprite, (TILE_SIZE, TILE_SIZE))

soundoff_sprite = pygame.image.load("Sprites/soundoff.png")
soundoff_sprite = pygame.transform.scale(soundoff_sprite, (TILE_SIZE, TILE_SIZE))

# initialize flag and bomb sprites
flag_sprite = pygame.image.load("Sprites/flag.png")
flag_sprite = pygame.transform.scale(flag_sprite, (TILE_SIZE, TILE_SIZE))

bomb_sprite = pygame.image.load("Sprites/bomb.png")
bomb_sprite = pygame.transform.scale(bomb_sprite, (TILE_SIZE, TILE_SIZE))
pygame.display.set_icon(bomb_sprite)

# sound effects
# pixabay.com for sounds
# mp3cut.net for easy in-browser editing
sound_on = True
shovel_sound = pygame.mixer.Sound("sounds/shovel.mp3")
shovel_sound.set_volume(0.5)  # 0.0 to 1.0
bomb_sound = pygame.mixer.Sound("sounds/bonk.mp3")
bomb_sound.set_volume(0.7)  # 0.0 to 1.0
win_sound = pygame.mixer.Sound("sounds/win.mp3")
win_sound.set_volume(0.4)  # 0.0 to 1.0
flag_sound = pygame.mixer.Sound("sounds/flag.mp3")
flag_sound.set_volume(0.1)

womps = [pygame.mixer.Sound("sounds/low.mp3"),
         pygame.mixer.Sound("sounds/med.mp3"),
         pygame.mixer.Sound("sounds/high.mp3")]

# clock
clock = pygame.time.Clock()
start_time = 0
win_time = 0
best_times = load_high_scores()  # dictionary


# cheat function that flags all the bombs
def reveal_all():
    global board
    global num_flags
    for tile in board.flat:
        if tile.flagged:
            tile.flagged = False
        if tile.is_bomb:
            tile.flagged = True
    num_flags = num_bombs


def start_game():
    global board
    global num_flags
    global game_lost
    global game_won
    global first_click
    global light_grass
    global dark_grass
    global light_tile
    global dark_tile
    global clock
    global start_time
    global difficulty_num

    # track start time
    start_time = pygame.time.get_ticks()

    board = np.empty((BOARD_WIDTH, BOARD_HEIGHT), dtype=object)
    # create board tiles
    for i in range(BOARD_WIDTH):
        for j in range(BOARD_HEIGHT):
            board[i][j] = Tile(i, j)

    create_bombs()

    num_flags = 0
    game_lost = False
    game_won = False
    first_click = True

    last_click_time = -1

    while True:
        # tick forward at 60 frames per second
        clock.tick(60)

        for event in pygame.event.get():
            # The pygame.QUIT event happens when someone tries to close the game window.
            if event.type == pygame.QUIT:
                save_high_score(best_times[difficulty_names[difficulty_num]])
                sys.exit()

            # pygame.MOUSEBUTTONDOWN occurs when the user clicks any mouse button
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Events will include what button was pushed, which you can check in if statements
                if event.button == pygame.BUTTON_LEFT:

                    if event.pos[1] > UI_height and not game_won and not game_lost:
                        if pygame.time.get_ticks() - last_click_time < 300:
                            click_tile(event.pos[0], event.pos[1], True)
                        else:
                            click_tile(event.pos[0], event.pos[1], False)
                        last_click_time = pygame.time.get_ticks()
                    else:
                        click_UI(event.pos[0], event.pos[1])

                elif event.pos[
                    1] > UI_height and event.button == pygame.BUTTON_RIGHT and not game_won and not game_lost:
                    flag_tile(event.pos[0], event.pos[1])

            if event.type == pygame.KEYDOWN:
                # KEYDOWN happens when a keyboard key is pressed. You can check the key with event.key.
                if event.key == pygame.K_SPACE:
                    # if spacebar is pressed, move tile colors around
                    temp = dark_grass
                    dark_grass = light_grass
                    light_grass = temp
                    temp = dark_tile
                    dark_tile = light_tile
                    light_tile = temp

                if event.key == pygame.K_0:  # 0 = insta win lol
                    reveal_all()

                if event.key == pygame.K_r:  # r is also reset
                    start_game()

        draw_sprites()
        draw_UI()

        # update screen
        pygame.display.flip()


start_game()
