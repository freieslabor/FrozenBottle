#!/usr/bin/env python3

# Interactive snake game controllable via left analog stick of Xbox Controller.

import argparse
import dataclasses
import enum
import random
import sys
import time
from copy import deepcopy

import hex as hexhelper
import LedClientBase as ledclientbase
from gamecontroller import GameController
#from fakecontroller import GameController

@enum.unique
class Element(enum.Enum):
    NOTHING = (0, 0, 0)
    HEAD = (1, 1, 1)
    DEAD = (0.5, 0.5, 0)
    CHERRY = (1, 0, 0)


@dataclasses.dataclass
class Cherry:
    field: hexhelper.HexBuff
    position: tuple[int] = (10, 8)

    def draw(self):
        # draw cherry
        self.field.set_wh(*self.position, Element.CHERRY.value)

    def _eat_cherry(self, position):
        if position != Element.CHERRY.value:
            return False

        # place cherry on random empty position
        while True:
            rand = random.randint(0, ledclientbase.NUMLEDS - 1)
            x, y = ledclientbase.seq_2_pos(rand)
            w, h = self.field.xy2wh(x, y)
            if self.field.get_wh(w, h) == Element.NOTHING.value:
                self.position = (w, h)
                return True


@dataclasses.dataclass
class Snake:
    field: hexhelper.HexBuff
    cherry: Cherry
    # head positions
    w: int
    h: int
    player_num: int
    last_direction: int = 1
    # head is part of tail
    tail: list[tuple] = dataclasses.field(default_factory=list)
    tail_length: int = 2
    game_over: bool = False

    player_colors = (
        (0, 1, 0),
        (0, 0, 1),
        (1, 0.8, 0.7),
        (0, 0.5, 0.2),
    )

    def _update(self):
        self.tail.append((self.w, self.h))

        # limit tail to tail_length
        while len(self.tail) > self.tail_length:
            del self.tail[0]

        self._draw()

    def _draw(self):
        # draw snake tail
        for (w, h) in self.tail:
            color = Element.DEAD.value if self.game_over else Snake.player_colors[self.player_num]
            self.field.set_wh(w, h, color)

        # draw snake head
        self.field.set_wh(self.w, self.h, Element.HEAD.value)

    def _is_out_of_bounds(self, w, h):
        x, y = self.field.wh2xy(w, h)
        seq = ledclientbase.pos_2_seq(x, y)
        return seq is None

    def move(self, direction, field_prev):
        # prevent reverse moves
        if direction == (self.last_direction + 3) % 6:
            direction = self.last_direction

        w = self.w + hexhelper.dir_wh[direction][0]
        h = self.h + hexhelper.dir_wh[direction][1]

        if self._is_out_of_bounds(w, h):
            self._draw()
            return

        destination_rgb = field_prev.get_wh(w, h)

        # collision: tail
        if destination_rgb == Snake.player_colors[self.player_num]:
            self.game_over = True
            self._draw()
            print(f"Game over: Snake {self.player_num} bit its tail")
            return

        # collision: cherry
        if self.cherry._eat_cherry(destination_rgb):
            self.tail_length += 1

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

    # build snake field filled with nothing
    field = ledclientbase.get_matching_HexBuff(0, 1)

    while True:
        controllers = []
        snakes = []
        field.fill_val(Element.NOTHING.value)

        cherry = Cherry(field)

        # init controllers
        try:
            for player_num in range(len(Snake.player_colors)):
                controllers.append(GameController(f"/dev/input/js{player_num}"))
                controllers[player_num].start()

                # init snake
                snakes.append(Snake(field, cherry, *field.xy2wh(3*player_num, 2*player_num), player_num))
        except FileNotFoundError:
            if len(controllers) == 0:
                print("No controllers connected", file=sys.stderr)
                sys.exit(1)

        while True:
            field_prev = deepcopy(field)

            # clear field
            field.fill_val(Element.NOTHING.value)

            for player_num in range(len(controllers)):
                # expecting a command from the controller on every query
                move_direction = controllers[player_num].getch()
                if not isinstance(move_direction, int):
                    move_direction = 1

                snakes[player_num].move(move_direction, field_prev)

            cherry.draw()

            # prepare sending data
            tx_data = []
            for j in range(ledclientbase.NUMLEDS):
                x, y = ledclientbase.seq_2_pos(j)
                rgb_tuple = field.get_xy(x, y)
                tx_data.append(ledclientbase.rgbF_2_bytes(rgb_tuple))

            # send data
            ledclientbase.send(b"".join(tx_data))

            if any([snake.game_over for snake in snakes]):
                time.sleep(10)
                break

            # loop-delay
            time.sleep(0.15)

    ledclientbase.closedown()

    return 0


if __name__=="__main__":
    sys.exit(main())
