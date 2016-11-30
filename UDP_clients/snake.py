#!/usr/bin/env python

# program to send some blinking to UDP for the flozen-bottle setup.


import socket
import time
import sys
import random
import argparse
import LedClientBase

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
		rotmap = (0,0,0,0,0,-1,-1,-1,1,1,1,2,-2)
		for j in xrange(20):
			d = rotmap[random.randint(0,len(rotmap)-1)]
			d = (self.prevdir+d+6)%6
			nx = self.x+self.field.dirs[d][0]
			ny = self.y+self.field.dirs[d][1]
			if not self.field.is_valid(nx,ny):
				continue
			_val = self.field.get(nx,ny)
			_val = (_val>>(8*self.index))&255
			if True:
				self.x = nx
				self.y = ny
				self.prevdir = d
				break



class hexfield(object):
	__slots__ = ('array','seq2array','array2seq','w','h','x0','y0','dirs')

	def __init__(self,first_row,num_leds,array_init_value):
		if (not isinstance(first_row,int)) or (first_row<2) or (first_row>256):
			raise ValueError("Bad value for first_row: %s"%repr(first_row))
		if (not isinstance(num_leds,int)) or (num_leds<2) or (num_leds>=0x0FFFF):
			raise ValueError("Bad value for num_leds: %s"%repr(num_leds))
		rup = 1 + (num_leds//(2*first_row-1))	# double-rows, somewhat too high.
		self.x0 = 1+rup
		self.y0 = 1
		self.w = self.x0+first_row+1
		self.h = self.y0+2*rup+1
		self.array = list((-1,))*(self.w*self.h)
		self.array2seq = list((-1,))*(self.w*self.h)
		self.seq2array = list((-1,))*num_leds
		_row=0;_p=0;_seq=0
		for _seq in xrange(num_leds):
			_iru = _seq%(2*first_row-1)
			_gol = _seq//(2*first_row-1)
			if _iru<first_row:
				x = self.x0-_gol+_iru
				y = self.y0+2*_gol
			else:
				x = self.x0-_gol+2*first_row-2-_iru
				y = self.y0+1+2*_gol
			self.seq2array[_seq] = ( x , y )
			self.array2seq[ x + self.w*y ] = _seq
			self.array[ x + self.w*y ] = array_init_value

		self.dirs = ((1,0),(1,-1),(0,-1),(-1,0),(-1,1),(0,1))

	def is_valid(self,x,y):
		try:
			return ( self.array2seq[x+self.w*y]>=0 )
		except IndexError:
			return False

	def get(self,x,y):
		pos = int(x+self.w*y)
		if self.array2seq[pos]<0:
			raise IndexError("outside of hexes-field")
		v = self.array[pos]
		return v

	def set(self,x,y,value):
		pos = int(x+self.w*y)
		if self.array2seq[pos]<0:
			raise IndexError("outside of hexes-field")
		self.array[pos] = value

	def coords2seq(self,x,y):
		res = self.array2seq[x+self.w*y]
		if res<0:
			raise IndexError("invalid coordinate")
		return res

	def seq2coords(self,seq_id):
		return self.seq2array[seq_id]

	def __iter__(self):
		return hexfield_iter(self)


class hexfield_iter(object):
	__slots__ = ('field','seq')
	def __init__(self,field):
		self.field = field
		self.seq = -1

	def next(self):
		self.seq += 1
		try:
			(x,y) = self.field.seq2coords(self.seq)
			pos = x + self.field.w*y
			return self.field.array[pos]
		except IndexError:
			self.seq -= 1
			raise StopIteration


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

	# build array matrix.
	field = hexfield(LedClientBase.LEN_FIRST_ROW,LedClientBase.NUMLEDS,0)
	glows = list()
	for i in xrange(3):
		(x,y) = field.seq2coords(i)
		glows.append( glow(field,x,y,i) )

	dirs = ((1,0),(1,-1),(0,-1),(-1,0),(-1,1),(0,1))


	for i in xrange(0x7FFF0000):

		# move
		for gl in glows:
			gl.move()

		# decay
		for j in xrange(LedClientBase.NUMLEDS):
			(x,y) = field.seq2coords(j)
			value = field.get(x,y)
			val1 = (value)&255 ; val2 = (value>>8)&255 ; val3 = (value>>16)&255
			val1 = max( val1-2 , 0 )
			val2 = max( val2-2 , 0 )
			val3 = max( val3-2 , 0 )
			field.set(x,y,(val1)+(val2<<8)+(val3<<16))
		# place self
		for i in xrange(3):
			x = glows[i].x ; y = glows[i].y
			value = field.get(x,y)
			value &= ~(0xFF<<(8*i))
			value |= 100<<(8*i)
			field.set(x,y,value)

		# convert to color-LED-string
		lin = list()
		for num in field:
			val1 = (num)&255 ; val2 = (num>>8)&255 ; val3 = (num>>16)&255
			_r = (255*val1)//100
			_g = (255*val2)//100
			_b = (255*val3)//100
			if val1==100 or val2==100 or val3==100:
				(_r,_g,_b) = (255,255,255)
			lin.append(chr(_r)+chr(_g)+chr(_b))
		#send
		LedClientBase.send("".join(lin))

		#loop-delay
		time.sleep(0.1)
		t += 0.100

	LedClientBase.closedown()

	return 0




if __name__=="__main__":
	sys.exit(main(sys.argv[1:]))
