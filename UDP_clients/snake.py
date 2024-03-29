#!/usr/bin/env python3

# program to send some blinking to UDP for the flozen-bottle setup.


import socket
import time
import sys
import random
import argparse
import LedClientBase
import hex

DEFAULT_PORT = 8901


class glow(object):
	__slots__ = ('field','x','y','prevdir','index')
	def __init__(self,field,x,y,index):
		self.field = field
		self.x=x
		self.y=y
		self.index=index
		self.prevdir=0

	def move(self):
		rotmap = (0,0,0,0,0,0,0,0,0,-1,-1,-1,-1,1,1,1,1,2,-2)
		for j in range(30):
			d = rotmap[random.randint(0,len(rotmap)-1)]
			d = (self.prevdir+d+6)%6
			nx = self.x+hex.dir_wh[d][0]
			ny = self.y+hex.dir_wh[d][1]
			_val = self.field.get_wh(nx,ny)
			if _val is None:
				continue
			_val = (_val>>(8*self.index))&255
			if True:
				self.x = nx
				self.y = ny
				self.prevdir = d
				break



def main(args):

	parser = argparse.ArgumentParser()
	parser.add_argument("address",type=str,help="UDP address")
	parser.add_argument("-p","--port",type=int,help="UDP port number")
	aa = parser.parse_args()

	print(repr(aa))

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

	# build array matrix.
	field = LedClientBase.get_matching_HexBuff(0,1)
	glows = list()
	for i in range(3):
		(w,h) = field.xy2wh(2+i+i,0)
		glows.append( glow(field,w,h,i) )

	dirs = hex.dir_wh


	for i in range(0x7FFF0000):

		# move
		for gl in glows:
			gl.move()

		# decay
		for j in range(LedClientBase.NUMLEDS):
			(x,y) = LedClientBase.seq_2_pos(j)
			value = field.get_xy(x,y)
			val1 = (value)&255 ; val2 = (value>>8)&255 ; val3 = (value>>16)&255
			val1 = max( val1-2 , 0 )
			val2 = max( val2-2 , 0 )
			val3 = max( val3-2 , 0 )
			field.set_xy(x,y,(val1)+(val2<<8)+(val3<<16))
		# place self
		for i in range(3):
			x = glows[i].x ; y = glows[i].y
			value = field.get_wh(x,y)
			value &= ~(0xFF<<(8*i))
			value |= 100<<(8*i)
			field.set_wh(x,y,value)

		# convert to color-LED-string
		lin = list()
		for j in range(LedClientBase.NUMLEDS):
			(xx,yy) = LedClientBase.seq_2_pos(j)
			num = field.get_xy(xx,yy)
			val1 = (num)&255 ; val2 = (num>>8)&255 ; val3 = (num>>16)&255
			if val1==100 or val2==100 or val3==100:
				val1, val2, val3 = 100, 100, 100
			lin.append(LedClientBase.rgbF_2_bytes((val1/100, val2/100, val3/100)))
		#send
		LedClientBase.send(b"".join(lin))

		#loop-delay
		time.sleep(0.1)
		t += 0.100

	LedClientBase.closedown()

	return 0




if __name__=="__main__":
	sys.exit(main(sys.argv[1:]))
