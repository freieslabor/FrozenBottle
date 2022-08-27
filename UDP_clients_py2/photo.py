#!/usr/bin/env python

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

	# create main 'framebuffer'
	mainbuff = hex.HexBuff(20,14,0,0,(0.0,0.0,0.0))

	# read image
	i = read_image(os.path.join("data","test.png"),mainbuff)

	# now connect to socket.
	LedClientBase.connect(address,port)



	t = 0.0

	for i in xrange(0x7FFF0000):


		# now prepare and send
		lin = list()
		for j in xrange(LedClientBase.NUMLEDS):
			(xx,yy) = LedClientBase.seq_2_pos(j)
			rgb_tuple = mainbuff.get_xy(xx,yy)

			lin.append(LedClientBase.rgbF_2_bytes(rgb_tuple))
		LedClientBase.send("".join(lin))

		time.sleep(0.250)
		t += 0.250

	LedClientBase.closedown()

	return 0


def read_image(name,buffer):
	if not isinstance(name,basestring):
		raise ValueError("expect string as name.")
	if not isinstance(buffer,hex.HexBuff):
		raise ValueError("expect hex.HexBuff object as buffer.")
	im = PIL.Image.open(name)
	W,H = im.size

	# scale down to at most MAXSIZE
	MAXSIZE=128
	fac = min((float(MAXSIZE)/W,float(MAXSIZE)/H))
	if fac<1.0:
		im = im.resize((int(W*fac+0.5),int(H*fac+0.5)))
		W,H = im.size

	im.convert("RGB")
	#im.show()

	# dead-inefficient loop.
	# for each pixel in graphic, sind hex-row above and below, and hex-cell before and after.
	# for these 4, calc distance and choose closest
	# for this hex, add to a running average.
	t = [(0,0,0,0)][:]*4096

	cos30 = math.cos(30*math.pi/180.0)
	HX_STEP = H/(12*cos30)	# base step size from one hex to neighbor.
	HX_ROWDIST = HX_STEP*cos30  # step size from one row to next vertically.
	print "HX_STEP = %.3f" % (HX_STEP,)
	print "HX_ROWDIST = %.3f" % (HX_ROWDIST,)

	for y in xrange(H):
		#print "y=%d" % y
		py = float(y)
		hy0 = int(py/HX_ROWDIST)*2
		hy1 = hy0+2
		for x in xrange(W):
			px = float(x)
			if (hy0&2):
				# odd line.
				hx00 = int(px/HX_STEP+0.5)*2-1
				hx10 = int(px/HX_STEP)*2
			else:
				# even line
				hx00 = int(px/HX_STEP)*2
				hx10 = int(px/HX_STEP+0.5)*2-1
			p = im.getpixel((x,H-1-y))
			# now find which is closest.
			po = ((hx00,hy0),(hx00+2,hy0),(hx10,hy1),(hx10+2,hy1))
			bd2 = 1.0e24
			b = 0
			for j in xrange(4):
				hx,hy = po[j]
				hx = HX_STEP*hx*0.5
				hy = HX_ROWDIST*hy*0.5
				#if x>=10 and x<18 and y>=10 and y<18:
				#	head = "px/py = (%5.2f/%5.2f)" % (px,py)
				#	if j>0: head = " "*len(head)
				#	print "%s    hx/hy = (%5.2f/%5.2f)" % (head,hx,hy)
				hx -= px
				hy -= py
				d2 = hx*hx + hy*hy
				if d2<bd2:
					bd2=d2;b=j
			hx,hy = po[b] # this is the hex-cell we map this pixel to.
			if hx>=0 and hy>=0 and hx<2*64 and hy<2*64:
				j = (hx>>1) + 64*(hy>>1)
				tt = t[j]
				t[j] = (tt[0]+1,tt[1]+p[0],tt[2]+p[1],tt[3]+p[2])

	for j in xrange(64):
		for i in xrange(64):
			tt = t[i+64*j]
			f = tt[0]*255.0
			if f>0.0:
				x = i+i+(j&1)
				y = j+j
				f = 1.0/f
				rgb = (float(tt[1])*f,float(tt[2])*f,float(tt[3])*f)
				buffer.set_xy(x,y,rgb)

	return True


if __name__=="__main__":
	sys.exit(main(sys.argv[1:]))
