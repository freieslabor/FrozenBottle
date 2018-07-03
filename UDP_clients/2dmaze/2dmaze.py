#!/usr/bin/env python

import os.path
import sys
# Add parent directory to import search path
sys.path.append(os.path.dirname(os.path.dirname( os.path.abspath(__file__) )))

import argparse
import math
import sys
import time
import LedClientBase

DEFAULT_PORT = 8901

TIMESTEP = 0.01

PRIMITIVEWALK_STEP_SIZE = 0.005

# for some reason, the six compat-module did not run properly on BBB.
try:
	xrange(1)
except NameError:
	xrange = range




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


	g = make_easy_grid()
	v = Viewer(resX=27,resY=27)
	w = Walker()


	for i in xrange(0x7FFF0000):

		w.step()
		x,y,r = w.getpos()
		#v.new_pos( 0.5,1.5 , math.pi*0.500*(i/20.0) )
		#v.new_pos( 0.5,1.01+i/4.0 , math.pi*0.50 )
		v.new_pos( x,y,r )

		va = v.view(g)


		# convert to FrozenBottle LED sequence
		seq = list()
		for i in xrange(LedClientBase.NUMLEDS):
			x,y = LedClientBase.seq_2_pos(i)
			if x>=0 and y>=0 and x<v.resX and y<v.resY:
				col = v.gfxmatrix[x+v.resX*y]
			else:
				col = 0
			seq.append( chr(col&255) + chr((col>>8)&255) + chr((col>>16)&255) )

		seq = "".join(seq)
		#print(repr(seq))

		LedClientBase.send("".join(seq))

		time.sleep(TIMESTEP)

	LedClientBase.closedown()

	return 0






""" List of 2D-Walls for a sort of Wolfenstein-3D graphic """

class Wall(object):
	__slots__ = ("x0","y0","x1","y1","color","walldir")
	def __init__(self,x0,y0,x1,y1):
		self.x0=float(x0)
		self.y0=float(y0)
		self.x1=float(x1)
		self.y1=float(y1)
		self.walldir=math.atan2(y1-y0,x1-x0)
		self.color = 0x00EE2211

	def hit(self,startX,startY,dx,dy):
		# zwei Geraden. erste: diese Wand, zweite, der Blickvektor.
		# Berechne Schnitt zweier Geraden in Punkt-Richtungsform, wie in der Schule
		# Ergebnis ist Distanz, oder None.
		Cx = startX-self.x0
		Cy = startY-self.y0
		# richtungsvektor diese Wand
		rx = self.x1-self.x0
		ry = self.y1-self.y0
		# Nenner-Determinante
		D = rx*(-dy) - ry*(-dx)
		if D*D < 1.0e-20:
			return None,False  # edges are too parallel.
		# Zaehler-Determinanten
		D1 = Cx*(-dy) - Cy*(-dx)
		D2 = rx*Cy - ry*Cx
		# lambdas ausrechnen.
		lmb1 = D1/D
		lmb2 = D2/D
		#print(D,D1,D2,lmb1,lmb2)
		if lmb1<0.0 or lmb1>1.0 or lmb2<=0.0:
			return None,False
		# Kreuzprodukt der Richtungsvektoren, um zu bestimmen, welche Seite der Wand.
		krz = rx*dy - ry*dx
		return lmb2,(krz>=0.0)


class Grid(object):
	__slots__=("walls")

	def __init__(self):
		self.walls=list()

	def add_wall(self,x0,y0,x1,y1):
		self.walls.append(Wall(x0,y0,x1,y1))

	def look_dir(self,startX,startY,dx,dy):
		# normalize dir-vector
		#tmp = 1.0/math.sqrt(dx*dx+dy*dy)
		#dx*=tmp
		#dy*=tmp
		# try all walls (BSP later??)
		bestdist=-1.0
		besthit=None
		bestside=False
		for wl in self.walls:
			dist,side = wl.hit(startX,startY,dx,dy)
			if dist is None:
				continue
			if (besthit is None) or dist<bestdist:
				besthit=wl
				bestdist=dist
				bestside=side
		if besthit is None:
			return None,None
		return besthit,bestdist,bestside

WALL_H = 1.0

class Viewer(object):
	__slots__=("posX","posY","angle","fow","resX","resY","gfxmatrix")
	def __init__(self,fow=math.pi/2.0,resX=28,resY=28):
		self.posX = 0.0
		self.posY = 0.0
		self.angle = 0.0
		self.fow = fow
		self.resX = resX
		self.resY = resY
		self.gfxmatrix = [0]*(self.resX*self.resY)

	def new_pos(self,x,y,angle=None):
		self.posX=x
		self.posY=y
		if angle is not None:
			self.angle = angle

	def view(self,grid):
		hits = self.view_calc_hits(grid)

		x = 0
		for (h,col,walldir) in hits:
			if col is None:
				continue
			# make y-range
			y0 = int( self.resY * (0.5 - h*0.5) + 0.5 )
			y1 = int( self.resY * (0.5 + h*0.5) + 0.5 )
			y0 = max(0,y0)
			y1 = min(self.resY,y1)

			# fill in
			for y in xrange(0,y0):
				self.gfxmatrix[x+self.resX*y] = 0
			for y in xrange(y0,y1):
				self.gfxmatrix[x+self.resX*y] = col
			for y in xrange(y1,self.resY):
				self.gfxmatrix[x+self.resX*y] = 0

			x+=1



	def view_calc_hits(self,grid):
		# calc the 2D view.
		# returns a list of 3-tuples. vis-height,color,wall-direction
		res = list()
		# view-vector
		vx = math.cos(self.angle)
		vy = math.sin(self.angle)
		# orthogonal step
		qsx = -vy
		qsy = vx
		# with of  orthogonal sampling edge
		wdd = math.sqrt( (math.cos(self.fow)-1.0)**2 + (math.sin(self.fow))**2 )
		#print("DEBUG: wdd = %f"%wdd)
		for i in xrange(self.resX):
			q = i/float(self.resX-1) - 0.5  # -1 .. 1
			q = -q ## lieber von links nach rechts.
			# sample view
			wall,dist,side = grid.look_dir( self.posX , self.posY , vx+qsx*wdd*q , vy+qsy*wdd*q )
			#print(wall,dist)
			if wall:
				# see a wall
				vis_height = WALL_H / (dist*wdd)
				walldir = wall.walldir
				if side:
					walldir += math.pi
				r,g,b = LedClientBase.hsv2rgb_float( walldir/(2.0*math.pi) , 0.8 , 1.0/max(1.0,math.pow(dist,1.0)) )
				color = int(r*255.0+0.5) + int(g*255.0+0.5)*0x0100 + int(b*255.0+0.5)*0x010000
			else:
				# looking into the void.
				walldir = 0.0
				color = None
				vis_height = 0.0
			res.append((vis_height,color,walldir))
		return res

	def debug_ascii_print(self):
		# ascii-art the output
		for y in range(self.resY):
			lin = ""
			for x in range(self.resX):
				c = self.gfxmatrix[x+self.resX*y]
				if c==0:
					lin = lin+" "
				else:
					r = (c>>0)&255
					let = 25*r/255.0
					lin = lin+chr(ord('A')+int(let))
			print(lin)


class Walker(object):
	def __init__(self):
		self.state=0.0


	def step(self):
		self.state += PRIMITIVEWALK_STEP_SIZE
		if self.state>=1.0:
			self.state-=1.0

	def getpos(self):
		s = self.state*4.0
		if s<1.0:
			return ( 2.5 , 1.5+4.0*s , math.pi*0.5 )
		s-=1.0
		if s<1.0:
			return ( 2.5 , 5.5 , math.pi*(0.5+s) )
		s-=1.0
		if s<1.0:
			return ( 2.5 , 5.5-4.0*s , math.pi*1.5 )
		s-=1.0
		return ( 2.5 , 1.5 , math.pi*(1.5-s) )



def make_easy_grid():
	g = Grid()
	g.add_wall( 0,0 , 5,0 )
	g.add_wall( 0,0 , 0,8 )
	g.add_wall( 0,1 , 1,1 )
	g.add_wall( 1,1 , 1,3 )
	g.add_wall( 1,3 , 2,3 )
	g.add_wall( 2,3 , 2,2 )
	g.add_wall( 2,1 , 3,1 )
	g.add_wall( 3,1 , 3,0 )
	g.add_wall( 0,4 , 2,4 )
	g.add_wall( 2,4 , 2,5 )
	g.add_wall( 2,5 , 1,5 )
	g.add_wall( 0,8 , 1,8 )
	g.add_wall( 1,8 , 1,6 )
	g.add_wall( 1,6 , 5,6 )
	g.add_wall( 5,6 , 5,0 )
	g.add_wall( 4,6 , 4,4 )
	g.add_wall( 3,5 , 3,2 )
	g.add_wall( 3,2 , 4,2 )
	g.add_wall( 4,3 , 5,3 )
	g.add_wall( 4,1 , 5,1 )
	return g


if __name__=="__main__":

	sys.exit(main(sys.argv[1:]))


	# to be used as lib, but test here.
	g = make_easy_grid()

	v = Viewer(resX=27,resY=27)

#	wall,dist = g.look_dir( 0.0,0.0 , 2.0,3.0 )
#	print("distance to hit: "+repr(dist))
#	wall,dist = g.look_dir( 0.0,0.0 , 3.0,2.0 )
#	print("distance to hit: "+repr(dist))

	w = Walker()

	for i in range(200):

		w.step()
		x,y,r = w.getpos()
		#v.new_pos( 0.5,1.5 , math.pi*0.500*(i/20.0) )
		#v.new_pos( 0.5,1.01+i/4.0 , math.pi*0.50 )
		v.new_pos( x,y,r )

		va = v.view(g)

		v.debug_ascii_print()


		time.sleep(0.1)

