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
	mainbuff = hex.HexBuff(20, 14, 0, 0, (0.2,0.2,0.2))

	# read image
	w,h,im = read_image(os.path.join("data","nyan.png"))

	# now connect to socket.
	LedClientBase.connect(address,port)

	w = w / 2
	for i in xrange(0x7FFF0000):
		for y in xrange(-int(h) + 42, 1, 14):
			for x in xrange(-w+14, 0, 1):
				mainbuff.blit(im, int(y*0.5-0.5)+x, y)

				# now prepare and send
				lin = list()
				for j in xrange(LedClientBase.NUMLEDS):
					(xx,yy) = LedClientBase.seq_2_pos(j)
					rgb_tuple = mainbuff.get_xy(xx,yy)
					r,g,b = rgb_tuple

					lin.append(LedClientBase.rgbF_2_bytes(rgb_tuple))
				LedClientBase.send("".join(lin))

				time.sleep(0.05)

	LedClientBase.closedown()

	return 0

def hex_round(q, r):
	# convert hex to cube
	x = q
	z = r
	y = -x-z

    # round cube coordinates
	rx = round(x)
	ry = round(y)
	rz = round(z)

	x_diff = abs(rx - x)
	y_diff = abs(ry - y)
	z_diff = abs(rz - z)

	if x_diff > y_diff and x_diff > z_diff:
		rx = -ry-rz
	elif y_diff > z_diff:
		ry = -rz-rz
	else:
		rz = -rx-ry

	# convert cube to hex
	q = rx
	r = ry

	return q, r

def pixel_to_hex(x, y, size):
	q = (x * math.sqrt(3)/3.0 - y / 3.0) / size
	r = y * 2.0/3 / size
	return hex_round(q, r)

def read_image(name):
	if not isinstance(name,basestring):
		raise ValueError("expect string as name.")
	im = PIL.Image.open(name)
	W,H = im.size

	W = int(W * 0.2 + 0.5)
	H = int(H * 0.2)
	W = W + (14 - W % 14)
	H = H + (14 - H % 14)

	im = im.resize((int(W),int(H)))
	W,H = im.size

	im.convert("RGB")
#	im.show()

	buffer = hex.HexBuff(W, H, 0, 0, (0.0, 0.0, 0.0))

	for x in xrange(W):
		for y in xrange(H):
			p = im.getpixel((x, y))
			#hx, hy = pixel_to_hex(x, y, 1)
			rgb = (float(p[0]/255.0), float(p[1]/255.0), float(p[2]/255.0))
			buffer.set_xy(x,H-y,rgb)

	return W, H, buffer


if __name__=="__main__":
	sys.exit(main(sys.argv[1:]))
