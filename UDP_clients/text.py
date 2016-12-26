#/usr/bin/env python

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
	parser.add_argument("text",type=str,help="Text")
	parser.add_argument("-p","--port",type=int,help="UDP port number")
	args = parser.parse_args()

#	print repr(aa)

	port = DEFAULT_PORT
	address = "127.0.0.1"
	if args.port is not None:
		port = args.port

	if port<=0 or port==0xFFFF:
		sys.stderr.write("bad port number %u\n"%port)
		return 1

	if args.address is not None:
		address = args.address

	LedClientBase.connect(address,port)
	
	mainbuff = hex.HexBuff(20,14,0,0,(0.0,0.0,0.0))
	mainbuff.fill_val((0.2,0.2,0.2))
		
	l = list()
	for i in range(len(args.text)):
            if (args.text[i] == "/"):
	        l.append(read_hex_file(os.path.join("data","slash.hex")))
            else:
	        l.append(read_hex_file(os.path.join("data",args.text[i]+".hex")))

	t = 0.0
	lr = -1
        length = 13
        for i in range(len(l)):
            length += 7
	for i in xrange(0x7FFF0000):

		# play
		mainbuff.fill_val((0.0,0.0,0.0))
		ii = (i%length)
                distance = 13
                for j in range(len(l)):
                    mainbuff.blit(l[j],distance - ii,4,None)
                    distance += 7

		# now prepare and send
		lin = list()
		for j in xrange(LedClientBase.NUMLEDS):
			(xx,yy) = LedClientBase.seq_2_pos(j)
			rgb_tuple = mainbuff.get_xy(xx,yy)

			lin.append(LedClientBase.rgbF_2_bytes(rgb_tuple))
		LedClientBase.send("".join(lin))

		time.sleep(0.03)
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
