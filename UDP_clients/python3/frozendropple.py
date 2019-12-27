import time
import random

from keyboard import Keyboard

import IPython
IPython.embed()

exit()

GLOBAL_LOCK = False

PALETTE = [
    [0, 0, 0],      # black
    [0, 0, 255],    # blue
    [255, 255, 0],  # yellow
    [255, 0, 0],    # red
    [0, 255, 0],    # green
]

client.sprite_mode = True


def gen_wall():
    gate_index = 7 + random.randint(-3, 4)
    sprite_spec = ''

    for i in range(0, 14):
        if i == gate_index:
            sprite_spec += '0 '

        else:
            sprite_spec += '1 '
    i *= -1
    
    sprite = Sprite(sprite_spec, palette=PALETTE, offset_y=14, offset_x=-1)
    sprite.type = 'wall'

    client.sprites.append(sprite)

def control_walls():
    gen_wall()

    while True:
        GLOBAL_LOCK = True

        walls = [i for i in client.sprites if i.type == 'wall']
        player = [i for i in client.sprites if i.type == 'player'][0]

        for wall in walls:
            wall.offset_y -= 1

            if wall.offset_y == player.offset_y:
                player.offset_y -= 1

        # last wall
        if walls[-1].offset_y == 11:
            gen_wall()

        # first wall
        if walls[0].offset_y == -1:
            client.sprites.remove(walls[0])

        GLOBAL_LOCK = False

        time.sleep(1)


def control_player():
    sprite = Sprite('2 ', palette=PALETTE, offset_x = 3)
    sprite.type = 'player'
    client.sprites.append(sprite)

    while True:
        if not GLOBAL_LOCK:
            client.move(sprite, 0, 1)

        # you win!
        if sprite.offset_y >= 13:
            client.sprite_mode = False
            client.sprites = []

            for x in range(14):
                for y in range(14):
                    client.buffer.set(x, y, 0, 255, 0)

            return

        time.sleep(0.5)


def left():
    player = [i for i in client.sprites if i.type == 'player'][0]
    player.offset_x -= 1


def right():
    player = [i for i in client.sprites if i.type == 'player'][0]
    player.offset_x += 1


worker_pool.executor.submit(control_player)
worker_pool.executor.submit(control_walls)

Keyboard = Keyboard()

Keyboard.capture(left=left, right=right)
