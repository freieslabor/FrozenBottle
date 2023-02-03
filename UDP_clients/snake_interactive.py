#!/usr/bin/env python3

# Interactive snake game controllable via left analog stick of Xbox Controller.

import argparse
import dataclasses
import enum
import random
import sys
import time

import hex as hexhelper
import LedClientBase as ledclientbase
from gamecontroller import GameController
#from fakecontroller import GameController


@enum.unique
class Element(enum.Enum):
    NOTHING = (0, 0, 0)
    HEAD = (1, 1, 1)
    TAIL = (0, 1, 0)
    DEAD = (0.5, 0.5, 0)
    CHERRY = (1, 0, 0)


@dataclasses.dataclass
class Snake:
    field: hexhelper.HexBuff
    # head positions
    w: int
    h: int
    last_direction: int = -1
    # head is part of tail
    tail: list[tuple] = dataclasses.field(default_factory=list)
    tail_length: int = 2
    cherry: tuple[int] = (10, 8)
    game_over: bool = False

    def _update(self):
        self.tail.append((self.w, self.h))

        # limit tail to tail_length
        while len(self.tail) > self.tail_length:
            del self.tail[0]

        self._draw()

    def _draw(self):
        # clear field
        self.field.fill_val(Element.NOTHING.value)

        # draw snake tail
        for (w, h) in self.tail:
            self.field.set_wh(w, h, Element.DEAD.value if self.game_over else Element.TAIL.value)

        # draw snake head
        self.field.set_wh(self.w, self.h, Element.HEAD.value)

        # draw cherry
        self.field.set_wh(*self.cherry, Element.CHERRY.value)

    def _is_out_of_bounds(self, w, h):
        x, y = self.field.wh2xy(w, h)
        seq = ledclientbase.pos_2_seq(x, y)
        return seq is None

    def _eat_cherry(self):
        self.tail_length += 1

        # place cherry on random empty position
        while True:
            rand = random.randint(0, ledclientbase.NUMLEDS - 1)
            x, y = ledclientbase.seq_2_pos(rand)
            w, h = self.field.xy2wh(x, y)
            if self.field.get_wh(w, h) == Element.NOTHING.value:
                self.cherry = (w, h)
                break

    def move(self, direction):
        # prevent reverse moves
        if direction == (self.last_direction + 3) % 6:
            direction = self.last_direction

        w = self.w + hexhelper.dir_wh[direction][0]
        h = self.h + hexhelper.dir_wh[direction][1]

        if self._is_out_of_bounds(w, h):
            return

        destination_rgb = self.field.get_wh(w, h)

        # collision: tail
        if destination_rgb == Element.TAIL.value:
            self.game_over = True
            self._draw()
            print("Game over: You bit yourself")
            return

        # collision: cherry
        if destination_rgb == Element.CHERRY.value:
            self._eat_cherry()

        self.w = w
        self.h = h
        self.last_direction = direction
        self._update()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("address", type=str, default="localhost", help="UDP address")
    parser.add_argument("-p", "--port", type=int, default=8901, help="UDP port number")
    args = parser.parse_args()

    if args.port <= 0 or args.port == 0xFFFF:
        print("bad port number {args.port}", file=sys.stderr)
        return 1

    if not ledclientbase.connect(args.address, args.port):
        return 1

    print(repr(args))

    controller = GameController()
    controller.start()

    # build snake field filled with nothing
    field = ledclientbase.get_matching_HexBuff(0, 1)
    field.fill_val(Element.NOTHING.value)

    snake = Snake(field, *field.xy2wh(2, 0))

    while True:
        # expecting a command from the controller on every query
        move_direction = controller.getch()
        if not isinstance(move_direction, int):
            continue

        snake.move(move_direction)

        # prepare sending data
        tx_data = []
        for j in range(ledclientbase.NUMLEDS):
            x, y = ledclientbase.seq_2_pos(j)
            rgb_tuple = field.get_xy(x, y)
            tx_data.append(ledclientbase.rgbF_2_bytes(rgb_tuple))

        # send data
        ledclientbase.send(b"".join(tx_data))

        if snake.game_over:
            break

        # loop-delay
        time.sleep(0.20)

    ledclientbase.closedown()

    return 0


if __name__=="__main__":
    sys.exit(main())
