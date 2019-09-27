import time
import random

GLOBAL_LOCK = False

PALETTE = [
    [0,   0,   0],
    [0, 0, 255],
    [255, 255, 0],
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
    sprite.is_wall = True

    client.sprites.append(sprite)

def controll_walls():
    gen_wall()

    while True:
        GLOBAL_LOCK = True

        walls = [i for i in client.sprites if i.is_wall]
        player = [i for i in client.sprites if not i.is_wall][0]

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


def controll_player():
    sprite = Sprite('2 ', palette=PALETTE, offset_x = 3)
    sprite.is_wall = False
    client.sprites.append(sprite)

    while True:
        if not GLOBAL_LOCK:
            client.move(sprite, 0, 1)

        time.sleep(0.3)

worker_pool.executor.submit(controll_player)
worker_pool.executor.submit(controll_walls)
