#!/usr/bin/env python3

# Not yet a scroll-text. But a base with a class for representing, blitting and rotating hex-patterns.


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
	parser.add_argument("address",type=str,help="UDP address")
	parser.add_argument("-p","--port",type=int,help="UDP port number")
	aa = parser.parse_args()

#	print(repr(aa))

	port = DEFAULT_PORT
	address = "127.0.0.1"
	if aa.port is not None:
		port = aa.port

	if port<=0 or port==0xFFFF:
		sys.stderr.write("bad port number %u\n"%port)
		return 1

	if aa.address is not None:
		address = aa.address

	LedClientBase.connect(address,port)

	mainbuff = hex.HexBuff(20,14,0,0,(0.0,0.0,0.0))
	mainbuff.fill_val((0.2,0.2,0.2))

	l = list()
	for i in range(10):
		l.append(read_hex_file(os.path.join("data","erlenmeier"+str(i)+".hex")))

	t = 0.0
	lr = -1
	for i in range(0x7FFF0000):

		# play
		mainbuff.fill_val((0.0,0.0,0.0))
		ii = (i%10)
		mainbuff.blit(l[ii],0,0,None)

		# now prepare and send
		lin = list()
		for j in range(LedClientBase.NUMLEDS):
			(xx,yy) = LedClientBase.seq_2_pos(j)
			rgb_tuple = mainbuff.get_xy(xx,yy)

			lin.append(LedClientBase.rgbF_2_bytes(rgb_tuple))
		LedClientBase.send(b"".join(lin))

		time.sleep(0.100)
		t += 0.100

	LedClientBase.closedown()

	return 0


def read_hex_file(name):
	v = hex.read_hex_file(name,True)
	w0,w1,h0,h1 = 0x10000,0,0x10000,0
	for x,y in v:
		h = y>>1
		w = ((x+h)>>1)
		w0=min(w,w0);w1=max(w,w1)
		h0=min(h,h0);h1=max(h,h1)
	res = hex.HexBuff(w1+1-w0,h1+1-h0,0,0,None)
	#res.fill_val((0.0,0.0,0.0))
	(ox,oy) = res.wh2xy(w,h)
	for x,y in v:
		h = y>>1
		w = ((x+h)>>1)
		col = v[(x,y)]
		if col is not None:
			res.set_wh(w-w0,h-h0,col)
	return res


if __name__=="__main__":
	sys.exit(main(sys.argv[1:]))
