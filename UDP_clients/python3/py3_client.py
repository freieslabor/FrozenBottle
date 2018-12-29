from concurrent.futures import ThreadPoolExecutor
from functools import partial
import asyncio
import curses
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

BLACK = bytearray([0, 0, 0])
RED = bytearray([255, 0, 0])


class Client:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address = (host, port)
        self.clear()
        self.sprites = []

    def clear(self):
        self.buffer = BLACK * TOTAL_LEDS

    def set(self, x, y, r, g, b):
        index = GRID[y][x]
        self.buffer[index*3:index*3+3] = r, g, b

    def write_sprites(self):
        self.clear()

        for sprite in self.sprites:
            for x in range(sprite.x):
                for y in range(sprite.y):
                    colors = sprite.get(x, y)

                    # skip black pixels
                    if not colors > BLACK:
                        continue

                    sprite_x = x + sprite.offset_x
                    sprite_y = y + sprite.offset_y

                    if y % 2 == 0 and not sprite_y % 2 == 0:
                        sprite_x += 1

                    self.set(sprite_x, sprite_y, *colors)

    def flush(self, interval=None):
        def _flush():
            self.write_sprites()
            self.socket.sendto(self.buffer, self.address)

        if interval:
            while True:
                _flush()
                time.sleep(interval)


class Sprite:
    def __init__(self, x=3, y=3, offset_x=0, offset_y=0):
        self.x = x
        self.y = y
        self.offset_x = offset_x
        self.offset_y = offset_y

        self.data = bytearray([0, 0, 255] * self.x * self.y)

    def get(self, x, y):
        i1 = (x + (y * self.x)) * 3
        i2 = i1 + 3

        return self.data[i1:i2]

    def set(self, x, y, r=0, g=0, b=0):
        i1 = (x + (y * self.x)) * 3
        i2 = i1 + 3

        self.data[i1:i2] = [r, g, b]

    def move_left(self):
        self.offset_x -= 1

    def move_right(self):
        self.offset_x += 1

    def move_down(self):
        self.offset_y += 1

    def move_up(self):
        self.offset_y -= 1


class WorkerPool:
    def __init__(self, loop=None, max_workers=4):
        self.loop = loop or asyncio.get_event_loop()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def run(self, func, *args, **kwargs):
        if not isinstance(func, partial):
            func = partial(func, *args, **kwargs)

        if not self.executor:
            return func()

        def _run(func, *args):
            try:
                future.set_result(func())

            except Exception as e:
                future.set_exception(e)

        future = asyncio.Future()
        self.loop.run_in_executor(self.executor, _run, func)

        return await future

class Keyboard:
    def __init__(self):
        self.running = True

    def capture(self, left=lambda: None, right=lambda: None, up=lambda: None,
                down=lambda: None):

        # get the curses screen window
        curses.filter()
        screen = curses.initscr()

        # turn off input echoing
        curses.noecho()

        # respond to keys immediately (don't wait for enter)
        curses.cbreak()

        # map arrow keys to special values
        screen.keypad(True)

        try:
            while self.running:
                char = screen.getch()

                if char == ord('q'):
                    break

                elif char == curses.KEY_RIGHT:
                    right()

                elif char == curses.KEY_LEFT:
                    left()

                elif char == curses.KEY_UP:
                    up()

                elif char == curses.KEY_DOWN:
                    down()

        finally:
            # shut down cleanly
            curses.nocbreak()
            screen.keypad(0)
            curses.echo()
            curses.endwin()
