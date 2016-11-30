#!/usr/bin/env python

# program to send some blinking to UDP for the flozen-bottle setup.


import time
import math
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

	if not LedClientBase.connect(address,port):
		return 1

	t = 0.0

	for i in xrange(0x7FFF0000):

		lin = list()
		for j in xrange(LedClientBase.NUMLEDS):
			(xx,yy) = LedClientBase.seq_2_pos(j)
			rgb_tuple = color_calc_func_1(i,j,xx,yy)
#			rgb_tuple = color_calc_func_2(i,j,xx,yy)


			xxx = list(rgb_tuple)
			xxx.sort()
		###	rgb_tuple = (xxx[1],xxx[2],xxx[0])


			lin.append(LedClientBase.rgbF_2_bytes(rgb_tuple))
		LedClientBase.send("".join(lin))

		time.sleep(0.040)
		t += 0.040

	LedClientBase.closedown()

	return 0



def color_calc_func_1(frameNo,seq_id,xx,yy):
	dot = (frameNo//7)%LedClientBase.NUMLEDS
	t = 0.017*frameNo
	if (frameNo&128)==0:
		col_cyc_idx = xx
	else:
		col_cyc_idx = yy
	if dot==seq_id:
		return (1.0,1.0,1.0)
	return LedClientBase.hsv2rgb_float(((t+0.125*col_cyc_idx)/3.0)%1.0,0.75,1.0)

def color_calc_func_2(frameNo,seq_id,xx,yy):
	xx = 0.5*(xx-13)
	yy = 0.4330127*(yy-6)		# sin(60deg)*0.5
	if xx==0.0 and yy==0.0:
		return (1.0,1.0,1.0)
	ang = math.atan2(yy,xx)
	h = ( ang*0.159154943 + 0.005*frameNo + 1.0 )%1.0
	return hsv2rgb_float( h , 0.6 , 0.8 )


if __name__=="__main__":
	sys.exit(main(sys.argv[1:]))
