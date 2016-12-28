#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# plasma in the frozen-bottle


import argparse
import math
import random
import sys
import time
import LedClientBase
import hex

DEFAULT_PORT = 8901


def main(args):

	parser = argparse.ArgumentParser()
	parser.add_argument("address",type=str,help="UDP address")
	parser.add_argument("-p","--port",type=int,help="UDP port number")
	aa = parser.parse_args()

	print repr(aa)

	port = DEFAULT_PORT
	address = "127.0.0.1"
	if aa.port is not None:
		port = aa.port

	if port<=0 or port==0xFFFF:
		sys.stderr.write("bad port number %u\n"%port)
		return 1

	if aa.address is not None:
		address = aa.address

	if not LedClientBase.connect(address,port):
		return 1

	t = 0.0
	vr = vg = vb = 0.0
	for i in xrange(0x7FFF0000):

		# make color-data for map
		lin = list()
		for j in xrange(LedClientBase.NUMLEDS):
			(xx,yy) = LedClientBase.seq_2_pos(j)
			val1 = math.sin(xx * 10 + t) + 1
			val2 = math.sin((xx * math.sin(t/2) + yy * math.cos(t/3))+t) + 1
			cx = xx + 0.5 * math.sin(t/5)
			cy = yy + 0.5 * math.cos(t/3)
			val3 = math.sin(math.sqrt(100 * (math.pow(cx,2) + math.pow(cy,2))+1+t)) + 1
			val = (val1 + val2 + val3) / 6
			vr = math.sin(val * math.pi + 2 * math.pi / 3 + t) + 1
			vg = math.sin(val * math.pi + 4 * math.pi / 3 + t) + 1
			vb = math.sin(val * math.pi + t) + 1
			rgb_tuple = (vr, vg, vb)
			lin.append(LedClientBase.rgbF_2_bytes(rgb_tuple))
		# send to strip
		LedClientBase.send("".join(lin))

		time.sleep(0.100)
		t += 0.100

	LedClientBase.closedown()

	return 0


if __name__=="__main__":
	sys.exit(main(sys.argv[1:]))
