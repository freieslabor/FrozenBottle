#!/usr/bin/env python

# Not yet a scroll-text. But a base with a class for representing, blitting and rotating hex-patterns.


import time
import math
import sys
import argparse
import LedClientBase

DEFAULT_PORT = 8901


class HexBuff(object):
	"""
		basically just a 2D array,
		with helper functions for hexes such as rotate and rot-paste and transform to x/y
		It uses two coordinate systems:
		w/h is a pair addressing the 2D array plain just like a 2D array.
		x/y is a pair transformed to a flat screen showing the hex-array. step-width is 2.
	"""
	__slots__ = ("data","w","h","ow","oh")

	XFORM_UNITY = (1,0,0,1)
	XFORM_FLIP_Y = (1,0,0,-1)
	XFORM_ROT60 = (1,-1,1,0)
	XFORM_ROT120 = (0,-1,1,-1)
	XFORM_ROT180 = (-1,0,0,-1)
	XFORM_ROT240 = (-1,1,-1,0)
	XFORM_ROT300 = (0,1,-1,1)

	def __init__(self,w,h,origin_w=0,origin_h=0,default_value=None):
		self.w = w
		self.h = h
		self.ow = origin_w
		self.oh = origin_h
		self.data = list()
		dum = list()
		for i in xrange(w):
			dum.append(default_value)
		for i in xrange(h):
			self.data.append(dum[:])

	def fill_val(self,val):
		for H in xrange(self.h):
			datalin = self.data[H]
			for W in xrange(self.w):
				datalin[W]=val

	def set_wh(self,w,h,val):
		if w<0 or w>=self.w or h<0 or h>=self.h:
			return
		self.data[h][w] = val

	def get_wh(self,w,h):
		if w<0 or w>=self.w or h<0 or h>=self.h:
			return 0
		return self.data[h][w]

	def set_xy(self,x,y,val):
		w,h = self.xy2wh(x,y)
		self.set_wh(w,h,val)

	def get_xy(self,x,y):
		w,h = self.xy2wh(x,y)
		return self.get_wh(w,h)

	def xy2wh(self,x,y):
		return (((x+(y>>1))>>1)+self.ow,(y>>1)+self.oh)

	def wh2xy(self,w,h):
		w-=self.ow
		h-=self.oh
		return (w+w-h,h+h)

	def blit(self,image,to_w,to_h,xform=None):
		if xform is None:
			xform = XFORM_UNITY
		# just plain, inefficient loops
		for H in xrange(image.h):
			datalin = image.data[H]
			oH = H-image.oh
			for W in xrange(image.w):
				val = datalin[W]
				if val is not None:
					oW = W-image.ow
					tw = xform[0]*oW + xform[1]*oH + self.ow + to_w
					th = xform[2]*oW + xform[3]*oH + self.oh + to_h
					self.set_wh(tw,th,val)


def main(args):

	ml = HexBuff(6,6,0,0,0)
	for h in xrange(6):
		l = list()
		for w in xrange(6):
			x,y = ml.wh2xy(w,h)
			W,H = ml.xy2wh(x,y)
			l.append("%2d/%2d..%2d/%2d"%(x,y,W,H))
		print "   ".join(l)

	print "------------"
	ls = list()
	for seq in xrange(LedClientBase.NUMLEDS):
		x,y = LedClientBase.seq_2_pos(seq)
		w,h = ml.xy2wh(x,y)
		ls.append((w,h))
	print " , ".join(("%d/%d"%(a,b)) for (a,b) in ls)


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

	mainbuff = HexBuff(20,14,0,0,(0.0,0.0,0.0))
	mainbuff.fill_val((0.2,0.2,0.2))

	over1 = HexBuff(7,3,3,1)
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
	rotpos.append(HexBuff.XFORM_UNITY)
	rotpos.append(HexBuff.XFORM_ROT60)
	rotpos.append(HexBuff.XFORM_ROT120)
	rotpos.append(HexBuff.XFORM_ROT180)
	rotpos.append(HexBuff.XFORM_ROT240)
	rotpos.append(HexBuff.XFORM_ROT300)

	t = 0.0
	lr = -1

	for i in xrange(0x7FFF0000):

		# play
		nr = int(t*2.5)%6
		if nr!=lr:
			lr = nr
			mainbuff.fill_val((0.2,0.2,0.2))
			mainbuff.blit(over1,9,4,rotpos[lr])



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


if __name__=="__main__":
	sys.exit(main(sys.argv[1:]))
