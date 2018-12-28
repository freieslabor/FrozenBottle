from concurrent.futures import ThreadPoolExecutor
from functools import partial
import asyncio
import socket
import time

DEFAULT_PORT = 8901
DEFAULT_HOST = 'localhost'

TOTAL_LEDS = 189

GRID = [
    [188, 187, 186, 185, 184, 183, 182, 181, 180, 179, 178, 177, 176],
    [162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175],
    [161, 160, 159, 158, 157, 156, 155, 154, 153, 152, 151, 150, 149],
    [135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148],
    [134, 133, 132, 131, 130, 129, 128, 127, 126, 125, 124, 123, 122],
    [108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121],
    [107, 106, 105, 104, 103, 102, 101, 100,  99,  98,  97,  96,  95],
    [ 81,  82,  83,  84,  85,  86,  87,  88,  89,  90,  91,  92,  93,  94],
    [ 80,  79,  78,  77,  76,  75,  74,  73,  72,  71,  70,  69,  68],
    [ 54,  55,  56,  57,  58,  59,  60,  61,  62,  63,  64,  65,  66,  67],
    [ 53,  52,  51,  50,  49,  48,  47,  46,  45,  44,  43,  42,  41],
    [ 27,  28,  29,  30,  31,  32,  33,  34,  35,  36,  37,  38,  39,  40],
    [ 26,  25,  24,  23,  22,  21,  20,  19,  18,  17,  16,  15,  14],
    [  0,   1,   2,   3,   4,   5,   6,   7,   8,   9,  10,  11,  12,  13],
]

DEFAULT_PALETTE = [
    [0, 0, 0],
    [255, 0, 0],
    [0, 0, 255],
    [0, 255, 255],
    [255, 255, 0],
]


class Sprite:
    def __init__(self, spec='', palette=DEFAULT_PALETTE, collision_check=True,
                 offset_x=0, offset_y=0):

        self.offset_x = offset_x
        self.offset_y = offset_y
        self.collision_check = collision_check

        self.spec = [i.replace(' ', '') for i in spec.splitlines() if i]

        self.x = len(self.spec[0])
        self.y = len(self.spec)

        data = []
        for line in self.spec:
            for i in line:
                data += palette[int(i)]

        self.data = bytearray(data)

    def get(self, x, y):
        i1 = (x + (y * self.x)) * 3
        i2 = i1 + 3

        return self.data[i1:i2]

    def set(self, x, y, r=0, g=0, b=0):
        i1 = (x + (y * self.x)) * 3
        i2 = i1 + 3

        self.data[i1:i2] = [r, g, b]


class Buffer:
    TRANSPARENT = bytearray([0, 0, 0])

    def __init__(self):
        self.clear()

    def clear(self):
        self.data = self.TRANSPARENT * TOTAL_LEDS

    def set(self, x, y, r, g, b):
        try:
            index = GRID[y][x]

        except IndexError:
            return

        self.data[index*3:index*3+3] = r, g, b

    def get(self, x, y):
        try:
            index = GRID[y][x]

        except IndexError:
            return self.TRANSPARENT

        return self.data[index*3:index*3+3]

    def write_sprites(self, sprites, collision_check=False, clear=True):
        if clear:
            self.clear()

        for sprite in sprites:
            if collision_check and not sprite.collision_check:
                continue

            for x in range(sprite.x):
                for y in range(sprite.y):
                    color = sprite.get(x, y)

                    if not color > self.TRANSPARENT:
                        continue

                    sprite_x = x + sprite.offset_x
                    sprite_y = y + sprite.offset_y

                    # x correction on short lines
                    if y % 2 == 0 and not sprite_y % 2 == 0:
                        sprite_x += 1

                    # handle out of bounds pixel
                    if sprite_y < 0 or sprite_y >= len(GRID):
                        continue

                    if sprite_x < 0 or sprite_x >= len(GRID[sprite_y]):
                        continue

                    # collision check
                    if collision_check:
                        if self.get(sprite_x, sprite_y) != self.TRANSPARENT:
                            return False

                    self.set(sprite_x, sprite_y, *color)

        return True


class Client:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address = (host, port)

        self.buffer = Buffer()

        self.sprite_mode = False
        self.sprites = []
        self.collision_buffer = Buffer()

    def flush(self, interval=None):
        def _flush():
            if self.sprite_mode:
                self.buffer.write_sprites(self.sprites)

            self.socket.sendto(self.buffer.data, self.address)

        if interval:
            while True:
                _flush()
                time.sleep(interval)

    def move(self, sprite, x, y):
        old_x = sprite.offset_x
        old_y = sprite.offset_y

        sprite.offset_x += x
        sprite.offset_y += y

        collision_check = self.collision_buffer.write_sprites(
            self.sprites, collision_check=True)

        if collision_check:
            self.buffer.write_sprites(self.sprites)

        else:
            sprite.offset_x = old_x
            sprite.offset_y = old_y

        return collision_check


if __name__ == '__main__':
    from argparse import ArgumentParser
    import runpy

    # parse args
    parser = ArgumentParser()

    parser.add_argument('script', type=str)
    parser.add_argument('--host', type=str, default=DEFAULT_HOST)
    parser.add_argument('--port', type=int, default=DEFAULT_PORT)
    parser.add_argument('--max-workers', type=int, default=4)
    parser.add_argument('--update-interval', type=float, default=0.2)

    args = parser.parse_args()

    # setup client
    client = Client(host=args.host, port=args.port)

    # setup worker
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=args.max_workers)

    # setup framebuffer task
    executor.submit(partial(client.flush, interval=args.update_interval))

    # run user script
    loop.run_until_complete(
        loop.run_in_executor(
            executor,
            partial(runpy.run_path, args.script, init_globals=globals())
        )
    )
