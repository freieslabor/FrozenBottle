#!/usr/bin/env python

# program to send some blinking to UDP for the flozen-bottle setup.

import argparse
import math
import os.path
import sys
import time
import LedClientBase
import hex

DEFAULT_PORT = 8901


def main(args):

    parser = argparse.ArgumentParser()
    parser.add_argument("address", type=str, help="UDP address")
    parser.add_argument("text", type=str, help="Text")
    parser.add_argument("-p", "--port", type=int, help="UDP port number")
    parser.add_argument("-r", "--revert", default=False, action="store_true")
    parser.add_argument("-d", "--dynamic", default=False, action="store_true")
    aa = parser.parse_args()

    print repr(aa)

    port = DEFAULT_PORT
    address = "127.0.0.1"
    if aa.port is not None:
        port = aa.port

    if port <= 0 or port == 0xFFFF:
        sys.stderr.write("bad port number %u\n" % port)
        return 1

    if aa.address is not None:
        address = aa.address

    if not LedClientBase.connect(address, port):
        return 1

    mainbuff = hex.HexBuff(20, 14, 0, 0, (0.0, 0.0, 0.0))
    mainbuff.fill_val((0.2, 0.2, 0.2))
    l = list()
    for i in range(len(aa.text)):
        if (aa.text[i] == "/"):
            l.append(read_hex_file(os.path.join("data", "slash.hex")))
        elif (aa.text[i] == "."):
            l.append(read_hex_file(os.path.join("data", "dot.hex")))
        else:
            l.append(read_hex_file(os.path.join("data", aa.text[i] + ".hex")))

    t = 0.0
    length = 13 + len(l) * 7

    for i in xrange(0x7FFF0000):
        ii = (i % length)
        distance = 13
        mainbuff.fill_val((0, 0, 0.01))
        for j in range(len(l)):
            f = 0.96
            if (aa.dynamic):
                y = 4 * math.sin(2 * math.pi * f * (distance - ii) + t) + 4
            else:
                y = 4
            if (aa.revert):
                mainbuff.blit(l[j], distance - ii, int(y), hex.HexBuff.XFORM_FLIP_X)
            else:
                mainbuff.blit(l[j], distance - ii, int(y), None)
            distance += 7

        lin = list()
        for j in xrange(LedClientBase.NUMLEDS):
            (xx, yy) = LedClientBase.seq_2_pos(j)
            rgb_tuple = mainbuff.get_xy(xx, yy)
            if (rgb_tuple == (1, 1, 1)):
                rgb_tuple = (0, 0, 0)
            if (rgb_tuple == (0, 0, 0.01)):
                rgb_tuple = color_calc_func_1(i, j, xx, yy)

            lin.append(LedClientBase.rgbF_2_bytes(rgb_tuple))
        LedClientBase.send("".join(lin))

        time.sleep(0.06)
        t += 0.1

    LedClientBase.closedown()

    return 0


def color_calc_func_1(frameNo, seq_id, xx, yy):
    dot = (frameNo // 7) % LedClientBase.NUMLEDS
    t = 0.017 * frameNo
    if (frameNo & 128) == 0:
        col_cyc_idx = xx
    else:
        col_cyc_idx = yy
    #if dot==seq_id:
    #	return (1.0,1.0,1.0)
    return LedClientBase.hsv2rgb_float(
        ((t + 0.125 * col_cyc_idx) / 3.0) % 1.0, 0.75, 1.0)


def read_hex_file(name):
    v = hex.read_hex_file(name, True)
    w0, w1, h0, h1 = 0x10000, 0, 0x10000, 0
    for x, y in v:
        h = y >> 1
        w = ((x + h) >> 1)
        w0 = min(w, w0)
        w1 = max(w, w1)
        h0 = min(h, h0)
        h1 = max(h, h1)
    res = hex.HexBuff(w1 + 1 - w0, h1 + 1 - h0, 0, 0, None)
    #res.fill_val((0.0,0.0,0.0))
    (ox, oy) = res.wh2xy(w, h)
    for x, y in v:
        h = y >> 1
        w = ((x + h) >> 1)
        col = v[(x, y)]
        if col is not None:
            res.set_wh(w - w0, h - h0, col)
    return res


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
