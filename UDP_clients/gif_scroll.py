#!/usr/bin/env python3

# Read an image, show statically.

import argparse
import math
import os.path
import PIL.Image
import sys
import time
import LedClientBase
import hex

DEFAULT_PORT = 8901


def main(args):

    parser = argparse.ArgumentParser()
    parser.add_argument("address", type=str, help="UDP address")
    parser.add_argument("-p", "--port", type=int, help="UDP port number")
    aa = parser.parse_args()

    #	print(repr(aa))

    port = DEFAULT_PORT
    address = "127.0.0.1"
    if aa.port is not None:
        port = aa.port

    if port <= 0 or port == 0xFFFF:
        sys.stderr.write("bad port number %u\n" % port)
        return 1

    if aa.address is not None:
        address = aa.address

    # create main 'framebuffer'
    mainbuff = hex.HexBuff(20, 14, 0, 0, (0.2, 0.2, 0.2))

    # now connect to socket.
    LedClientBase.connect(address, port)

    img = PIL.Image.open(os.path.join("data", "nyan.gif"))
    img.seek(0)
    w, h = img.size
    colors = getPaletteInRgb(img)

    buffer = hex.HexBuff(w*2, h*2, 0, 0, (0.2, 0.2, 0.2))

    get_image(img, colors, buffer)

    for i in range(0x7FFF0000):
        for x in range(-w+14, 0, 1):
            for i in range(3):
                img.seek(x % 4 * 3 + i)
                get_image(img, colors, buffer)

                mainbuff.blit(buffer, x, -1)
                # now prepare and send
                lin = list()
                for j in range(LedClientBase.NUMLEDS):
                    (xx, yy) = LedClientBase.seq_2_pos(j)
                    rgb_tuple = mainbuff.get_xy(xx, yy)
                    r, g, b = rgb_tuple

                    lin.append(LedClientBase.rgbF_2_bytes(rgb_tuple))
                LedClientBase.send(b"".join(lin))

                time.sleep(0.08)

            time.sleep(0.05)

    LedClientBase.closedown()

    return 0

def chunk(seq, size, groupByList=True):
    """Returns list of lists/tuples broken up by size input"""
    func = tuple
    if groupByList:
        func = list
    return [func(seq[i:i + size]) for i in range(0, len(seq), size)]


def getPaletteInRgb(img):
    """
    Returns list of RGB tuples found in the image palette
    :type img: Image.Image
    :rtype: list[tuple]
    """
    assert img.mode == 'P', "image should be palette mode"
    pal = img.getpalette()
    colors = chunk(pal, 3, False)
    return colors

def get_image(img, colors, buffer):
    W, H = img.size
    for x in range(W):
        for y in range(H):
            p = img.getpixel((x, y))
            try:
                p = colors[p]
            except TypeError:
                pass
            rgb = (float(p[0] / 255.0),
                   float(p[1] / 255.0),
                   float(p[2] / 255.0))

            buffer.set_xy(x*2, (H-y)*2, rgb)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
