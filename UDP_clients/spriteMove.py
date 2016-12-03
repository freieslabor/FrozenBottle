#!/usr/bin/env python

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

#	print repr(aa)

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

	over1 = hex.HexBuff(7,3,3,1)
	over1.fill_val((0.9,0.3,0.2))
	over1.set_wh(3,1,(0.9,0.9,0.9))
	over1.set_wh(1,0,(0.3,0.9,0.4))
	over1.set_wh(0,0,(0.3,0.9,0.4))
	over1.set_wh(0,1,(0.3,0.9,0.4))
	over1.set_wh(0,2,(0.3,0.9,0.4))
	over1.set_wh(6,0,None)
	over1.set_wh(5,0,None)
	over1.set_wh(6,1,None)
	rotpos = list()
	rotpos.append(hex.HexBuff.XFORM_UNITY)
	rotpos.append(hex.HexBuff.XFORM_ROT60)
	rotpos.append(hex.HexBuff.XFORM_ROT120)
	rotpos.append(hex.HexBuff.XFORM_ROT180)
	rotpos.append(hex.HexBuff.XFORM_ROT240)
	rotpos.append(hex.HexBuff.XFORM_ROT300)
	rotpos.append(hex.HexBuff.XFORM_UNITY)
	rotpos.append(hex.HexBuff.XFORM_FLIP_X)
	rotpos.append(hex.HexBuff.XFORM_UNITY)
	rotpos.append(hex.HexBuff.XFORM_FLIP_Y)

	over2 = read_hex_file(os.path.join("data","sample.hex"))

	t = 0.0
	lr = -1

	for i in xrange(0x7FFF0000):

		# play
		nr = int(t*2.5)%len(rotpos)
		mainbuff.fill_val((0.2,0.2,0.2))
		mainbuff.blit(over1,9,4,rotpos[nr])
		mainbuff.blit(over2,10,(i%20)-7,None)



		# now prepare and send
		lin = list()
		for j in xrange(LedClientBase.NUMLEDS):
			(xx,yy) = LedClientBase.seq_2_pos(j)
			rgb_tuple = mainbuff.get_xy(xx,yy)

			lin.append(LedClientBase.rgbF_2_bytes(rgb_tuple))
		LedClientBase.send("".join(lin))

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
