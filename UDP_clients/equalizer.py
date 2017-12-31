#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
from equalizer_recorder import *
import sys
import LedClientBase
import hex
import argparse

MATR_SIZE = 14


class Visualization:
    def __init__(self, address, port, minNum, maxNum):
        "Ininitializes a new pygame screen using the framebuffer"

        self.minNum = minNum
        self.maxNum = maxNum

        LedClientBase.connect(address, port)

        self.rgb_matr = [[(100, 100, 100) for v in range(MATR_SIZE)] for i in
                         range(MATR_SIZE)]

        self.initRecorder()

    def initRecorder(self):
        self.SR = SwhRecorder()
        self.SR.setup()
        self.SR.continuousStart()

    def translate(self, value, leftMin, leftMax, rightMin, rightMax):
        # Figure out how 'wide' each range is
        leftSpan = leftMax - leftMin
        rightSpan = rightMax - rightMin

        # Convert the left range into a 0-1 range (float)
        valueScaled = float(value - leftMin) / float(leftSpan)

        # Convert the 0-1 range into a value in the right range.
        return rightMin + (valueScaled * rightSpan)

    def show(self):
        run = True
        maxAvg = 1
        lastMapped = 0
        tendency = 0
        mapped = 0
        while run:
            try:
                if self.SR.newAudio:
                    # fourier transformation
                    fft = self.SR.fft()[1]
                    self.SR.newAudio = False

                    avg = reduce(lambda x, y: x + y, fft) / len(fft)

                    # dynamic maximum
                    if avg > maxAvg:
                        maxAvg = avg

                    # translate range into number of frames
                    mapped = self.translate(avg, 0, maxAvg, self.minNum, self.maxNum)

                    # do not update if image does not change
                    if mapped == lastMapped:
                        continue
                    elif mapped > lastMapped:
                        tendency = 1
                    elif mapped < lastMapped:
                        tendency = -1

                    # smooth transition
                    if lastMapped - mapped > 2:
                        mapped = lastMapped - ((lastMapped - mapped)/2)

                    # save last image
                    lastMapped = mapped
                    #print "calcd"
                else:
                    mapped = lastMapped + tendency
                    if not self.minNum <= mapped <= self.maxNum:
                        continue
                    #print "tendency"
    
                print(mapped)
                hexmap = LedClientBase.get_matching_HexBuff()
                for k in range(14):
                    for j in range(14):
                        if k == 0:
                            if j <= (int)(mapped):
                                hexmap.set_xy(k, j, LedClientBase.rgbF_2_bytes((100, 100, 100)))
                            else:
                                hexmap.set_xy(k, j, LedClientBase.rgbF_2_bytes((0, 0, 0)))
                        else:
                            hexmap.set_xy(k, j, LedClientBase.rgbF_2_bytes((100, 100, 100)))
                llist = list()
                a = ""
                for k in range(LedClientBase.NUMLEDS):
                    print(k)
                    (xx, yy) = LedClientBase.seq_2_pos(k)
                    rgb_tuple = hexmap.get_xy(xx, yy)
                    #a += rgb_tuple
                    print(rgb_tuple)
                LedClientBase.send(a)

                # give it a second until the audio buffer is filled up
                time.sleep(0.11)
            except:
                break
        self.SR.close()
        LedClientBase.closedown()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "address",
        type=str,
        help="UDP address",
        default="127.0.0.1"
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        help="UDP port number",
        default=8901
    )
    options = parser.parse_args()

    if not (0 <= options.port <= 65535):
        sys.stderr.write("bad port number %u\n" % options.port)
        sys.exit(1)

    if not LedClientBase.connect(options.address, options.port):
        sys.stderr.write("connect failed\n")
        sys.exit(1)

    v = Visualization(options.address, options.port, 0, MATR_SIZE)
    v.show()
