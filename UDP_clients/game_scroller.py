#!/usr/bin/env python3

# Interactive snake game controllable via analog stick of Xbox Controller.

import time
import sys
import argparse
import LedClientBase
import hex
import gamecontroller

DEFAULT_PORT = 8901


landscape = """

#
##
#
#
##
###
####
####
###
##
#
#
##
##
##
###
### 
#####
##
##
#
#
##
######
#####
##
##
#
#............#
#...........##
#...........##
###.........##
#####....#####
#####....#####
#####....#####
#####....#####
####.........#
###
###
WW
WW
WW
WW
WW
WW
WW
WW
######
######
######
######
######
######
######








"""

land = list()

llmap = {' ':0,'.':0,'0':0,'#':0x227777,'X':0x335588,'W':0x662211}

def convert_land():
	global land
	land = list()
	for L in landscape.split('\n'):
		L = L+'                           '
		Lr = tuple(llmap[b] for b in L[:14])
		land.append(Lr)

class item(object):
	__slots__ = ('field','x','y','colorval','markdel')
	def __init__(self,field,x,y,colorval):
		self.field = field
		self.x=x
		self.y=y
		self.colorval=colorval
		self.markdel = False

	def move(self,d):
		pass


class ship(item):
	__slots__ = ()
	def __init__(self,field,x,y,colorval):
		super().__init__(field,x,y,colorval)

	def move(self, d):
		if d>=0:
			nx = self.x+hex.dir_wh[d][0]
			ny = self.y+hex.dir_wh[d][1]
		else:
			nx = self.x
			ny = self.y
#		nx = min(max(nx,0),11)
#		ny = min(max(ny,0),13)
		value = self.field.get_wh(nx,ny)
		if value is not None:
			self.x = nx
			self.y = ny
			if value!=0:
				pass # boom.

class bullet(item):
	__slots__ = ()
	def __init__(self,field,x,y):
		super().__init__(field,x,y,0x444444)

	def move(self, d):
		nx = self.x+1

		value = self.field.get_wh(nx,self.y)
		if value is None:
			self.markdel = True
		else:
			self.x = nx



def main(args):

	parser = argparse.ArgumentParser()
	parser.add_argument("address",type=str,help="UDP address")
	parser.add_argument("-p","--port",type=int,help="UDP port number")
	aa = parser.parse_args()

	print(repr(aa))

	global land
	convert_land()
	print(repr(land))

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
	ships = list()
	playership = ship(field,4,6,0x777777)
	ships.append( playership )

	T=0
	Bfire = False

	for i in range(0x7FFF0000):
		cc = tio.get_axis6()

		# move
		T+=1
		for gl in ships:
			gl.move(cc)

		# fire
		_v = tio.get_button('a')
		if _v and not Bfire:
			print("peng.")
			ships.insert(0,bullet(field,playership.x,playership.y))

		Bfire = _v

		# scroll left
		mapX = (T%len(land))
		for y in range(1,field.h-1):
			datrow = field.data[y]
			for x in range(field.w-1):
				if datrow[x] is None:
					continue
				value = datrow[x+1]
				if value is None:
					lval = land[T%len(land)][y-1]
					value = lval	# todo  colormap
				datrow[x] = value

		shmap = dict()
		# place self
		i=0
		while i<len(ships):
			shp = ships[i]
			if shp.markdel:
				del ships[i]
				print("removed")
				continue
			i += 1
			x = shp.x ; y = shp.y
			x,y = field.wh2xy(x,y)
			shmap[(x,y)] = shp.colorval
		#print(cc,repr(shmap))


		# convert to color-LED-string
		lin = list()
		for j in range(LedClientBase.NUMLEDS):
			(xx,yy) = LedClientBase.seq_2_pos(j)
			num = field.get_xy(xx,yy)

			if (xx,yy) in shmap:
				num = shmap[(xx,yy)]

			val1 = (num)&255 ; val2 = (num>>8)&255 ; val3 = (num>>16)&255


			if False:#True:
				yy=int(yy/2)
				xx=int(xx/2)
				xx = (xx+T)%len(land)
				if yy<14:
					lval = land[xx][yy]
					if lval>0:
						val1=val2=99*lval
						val3=20*lval
			lin.append(bytes((val1, val2, val3)))
			#lin.append(LedClientBase.rgbF_2_bytes((val1/100.0, val2/100.0, val3/100.0)))
		# send
		LedClientBase.send(b"".join(lin))

		# loop-delay
		time.sleep(0.1)

	LedClientBase.closedown()

	return 0


if __name__=="__main__":
	sys.exit(main(sys.argv[1:]))
