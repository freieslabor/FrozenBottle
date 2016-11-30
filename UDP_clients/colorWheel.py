#!/usr/bin/env python

# program to send some blinking to UDP for the flozen-bottle setup.


import time
import math
import sys
import argparse
import LedClientBase

DEFAULT_PORT = 8901

ORIGIN_X = 13
ORIGIN_Y = 5*2
SCALE_X = 0.5
SCALE_Y = 0.5*math.cos(30*math.pi/180.0)
TIMESTEP = 0.067
ROTSPEED = 0.5 # rotations/sec

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
			rgb_tuple = color_calc_func_3(i,j,xx,yy)


			xxx = list(rgb_tuple)
			xxx.sort()
		###	rgb_tuple = (xxx[1],xxx[2],xxx[0])


			lin.append(LedClientBase.rgbF_2_bytes(rgb_tuple))
		LedClientBase.send("".join(lin))

		time.sleep(TIMESTEP)
		t += TIMESTEP

	LedClientBase.closedown()

	return 0



def color_calc_func_3(frameNo,seq_id,xx,yy):
	x = (xx-ORIGIN_X)*SCALE_X
	y = (yy-ORIGIN_Y)*SCALE_Y
	r2 = x*x+y*y
	if r2<=0.25:
		return (1.0,1.0,1.0)
	t = frameNo*TIMESTEP
	ang = math.atan2(y,x)
	rad = math.sqrt(r2)
	ang += (((frameNo*TIMESTEP*ROTSPEED)%1.0)*2.0*math.pi)
	ang -= 0.02*r2
	# scale ang to 0..1
	ang = (ang/(math.pi*2.0)+4.0)%1.0
	if ang<0.5:
		ang = ang*2.0
		ang = 1.0-ang
		return (ang*0.2,ang*1.0,ang*0.4)
	else:
		ang = (ang-0.5)*2.0
		ang = 1.0-ang
		return (ang*0.9,ang*0.9,ang*0.1)



if __name__=="__main__":
	sys.exit(main(sys.argv[1:]))
