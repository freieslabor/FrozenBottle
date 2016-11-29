#!/usr/bin/env python

# program to send some blinking to UDP for the flozen-bottle setup.


import time
import sys
import argparse
import LedClientBase

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

	LedClientBase.connect(address,port)

	t = 0.0

	for i in xrange(0x7FFF0000):

		lin = list()
		for j in xrange(LedClientBase.NUMLEDS):
			(xx,yy) = LedClientBase.seq_2_pos(j)
			rgb_tuple = (0.0,0.0,1.0)
			if (i%10)==2:
				rgb_tuple = (0.1,0.1,0.1)
			if (i%LedClientBase.NUMLEDS)==j:
				rgb_tuple = (1.0,1.0,1.0)

			lin.append(LedClientBase.rgbF_2_bytes(rgb_tuple))
		LedClientBase.send("".join(lin))

		time.sleep(0.040)
		t += 0.040

	LedClientBase.closedown()

	return 0



if __name__=="__main__":
	sys.exit(main(sys.argv[1:]))
