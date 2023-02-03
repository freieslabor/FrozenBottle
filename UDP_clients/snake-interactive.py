#!/usr/bin/env python3

# Interactive snake game controllable via analog stick of Xbox Controller.

import time
import sys
import argparse
import LedClientBase
import hex
import gamecontroller

DEFAULT_PORT = 8901


class glow(object):
	__slots__ = ('field','x','y','prevdir','index')
	def __init__(self,field,x,y,index):
		self.field = field
		self.x=x
		self.y=y
		self.index=index
		self.prevdir=0

	def move(self, d):
		nx = self.x+hex.dir_wh[d][0]
		ny = self.y+hex.dir_wh[d][1]
		_val = self.field.get_wh(nx,ny)
		if _val is None:
			return
		_val = (_val>>(8*self.index))&255
		self.x = nx
		self.y = ny
		self.prevdir = d



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

	tio = gamecontroller.GameController()
	tio.start()

	# build array matrix.
	field = LedClientBase.get_matching_HexBuff(0,1)
	glows = list()
	for i in range(3):
		(w,h) = field.xy2wh(2+i+i,0)
		glows.append( glow(field,w,h,i) )

	for i in range(0x7FFF0000):
		cc = tio.getch()
		if not isinstance(cc, int):
			continue

		# move
		for gl in glows:
			gl.move(cc)

		# decay
		for j in range(LedClientBase.NUMLEDS):
			(x,y) = LedClientBase.seq_2_pos(j)
			value = field.get_xy(x,y)
			val1 = (value)&255 ; val2 = (value>>8)&255 ; val3 = (value>>16)&255
			val1 = max( val1-5 , 0 )
			val2 = max( val2-5 , 0 )
			val3 = max( val3-5 , 0 )
			field.set_xy(x,y,(val1)+(val2<<8)+(val3<<16))

		# place self
		for i in range(1):
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
			# white snake head
			if val1==100 or val2==100 or val3==100:
				val1, val2, val3 = 100, 100, 100
			lin.append(LedClientBase.rgbF_2_bytes((val1/100, val2/100, val3/100)))
		# send
		LedClientBase.send(b"".join(lin))

		# loop-delay
		time.sleep(0.1)

	LedClientBase.closedown()

	return 0


if __name__=="__main__":
	sys.exit(main(sys.argv[1:]))
