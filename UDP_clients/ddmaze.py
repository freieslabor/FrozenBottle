#!/usr/bin/env python

import argparse
import math
import sys
import time
import LedClientBase
import random
import noncanon_input

DEFAULT_PORT = 8901

TIMESTEP = 0.003

PRIMITIVEWALK_STEP_SIZE = 0.005

SIZE = 3

SEED = int(time.time())

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
        print(aa)
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

        gen = generator(SIZE,SEED)
        grid, knots = gen.generate()
        gen.print_map()
        io = noncanon_input.cio()
        w = Walker(math.pi, gen.start, knots)
        w = InteractiveWalker(io, gen.start, gen.walls)
        v = Viewer(resX=27,resY=27,fow=2.5)

	while w.move():

		x,y,r = w.getpos()
		#v.new_pos( 0.5,1.5 , math.pi*0.500*(i/20.0) )
		#v.new_pos( 0.5,1.01+i/4.0 , math.pi*0.50 )
		v.new_pos( x,y,r )

		va = v.view(grid)


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

		LedClientBase.send("".join(seq))
                w.move()

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
        
        def p(self):
            print("("+str(self.x0)+","+str(self.y0)+"),("+str(self.x1)+","+str(self.y1)+")")

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
			return None, None, None
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
		wdd = 0.5*math.sqrt( (math.cos(self.fow)-1.0)**2 + (math.sin(self.fow))**2 )
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
				r,g,b = LedClientBase.hsv2rgb_float( ((walldir+0.3)/(2.0*math.pi))%1.0 , 0.8 
                                        , 1.0/max(1.0,2.0*math.pow(dist,0.8)) )
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

class knot(object):

    def __init__(self, xpos, ypos, is_start=False, is_goal=False):
        self.north = None
        self.east = None
        self.south = None
        self.west = None
        self.is_start = is_start
        self.is_goal = is_goal
        self.pos = (xpos, ypos)
        self.neightbors = list()

    def getdist(self,other_knot):
        distx = self.pos[0] - other_knot.pos[0]
        disty = self.pos[1] - other_knot.pos[1]
        return math.sqrt(distx**2 + disty**2)

    def setNeightbor(self, north=None, east=None, south=None, west=None):
        self.north = north
        self.east = east
        self.south = south
        self.west = west

    def getNeightbor(self):
        return self.neightbors

    def gen(self,start,seed,size):
        th = 75
        #north 
        self.neightbors = list()
        random.seed(str(seed) + str((self.pos[0],self.pos[1])) + str((self.pos[0],self.pos[1]+1)))
        if random.randint(0,100) < th:
            self.north = knot(self.pos[0], self.pos[1]+1)
            self.neightbors.append(self.north)
            if self.north.getdist(start) > size:
                self.neightbors.remove(self.north)
                self.north = None
        #east  
        random.seed(str(seed) + str((self.pos[0],self.pos[1])) + str((self.pos[0]+1,self.pos[1])))
        if random.randint(0,100) < th:
            self.east = knot(self.pos[0]+1, self.pos[1])
            self.neightbors.append(self.east)
            if self.east.getdist(start) > size:
                self.neightbors.remove(self.east)
                self.east = None
        #south  
        random.seed(str(seed) + str((self.pos[0],self.pos[1]-1)) + str((self.pos[0],self.pos[1])))
        if random.randint(0,100) < th:
            self.south = knot(self.pos[0], self.pos[1]-1)
            self.neightbors.append(self.south)
            if self.south.getdist(start) > size:
                self.neightbors.remove(self.south)
                self.south = None
        #west  
        random.seed(str(seed) + str((self.pos[0]-1,self.pos[1])) + str((self.pos[0],self.pos[1])))
        if random.randint(0,100) < th:
            self.west = knot(self.pos[0]-1, self.pos[1])
            self.neightbors.append(self.west)
            if self.west.getdist(start) > size:
                self.neightbors.remove(self.west)
                self.west = None
        return self.neightbors

    def getWalls(self):
        walls = list()
        if not self.north:
            walls.append(Wall(self.pos[0]-0.5,self.pos[1]+0.5,self.pos[0]+0.5,self.pos[1]+0.5))
        if not self.east:
            walls.append(Wall(self.pos[0]+0.5,self.pos[1]+0.5,self.pos[0]+0.5,self.pos[1]-0.5))
        if not self.south:
            walls.append(Wall(self.pos[0]-0.5,self.pos[1]-0.5,self.pos[0]+0.5,self.pos[1]-0.5))
        if not self.west:
            walls.append(Wall(self.pos[0]-0.5,self.pos[1]+0.5,self.pos[0]-0.5,self.pos[1]-0.5))
        return walls

class generator(object):

    def __init__(self,size,seed):
        self.start = knot(0.5,0.5,is_start=True)
        self.size = 5
        self.knots = list()
        self.size = size
        self.walls = list()
        self.grid = Grid()
        self.seed = seed

    def generate(self):
        seed = self.seed
        tmp_knots = list()
        tmp_knots.append(self.start)
        while tmp_knots:
            knot = tmp_knots.pop()
            self.knots.append(knot)
            for i in knot.gen(self.start,seed,self.size):
                a = True
                for j in self.knots:
                    if i.pos == j.pos:
                        a = False
                if a:
                    tmp_knots.append(i)
        self.knots.remove(self.start)
        self.knots[random.randint(1,len(self.knots))-1].is_goal=True
        self.knots.append(self.start)
        self.buildWalls()
        for i in self.walls:
            print i.p()
        #self.reduceWalls()
        self.grid.walls = self.walls
        for i in self.walls:
            print i.p()
        return self.grid, self.knots

    def buildWalls(self):
        for i in self.knots:
            self.walls.extend(i.getWalls())
      
    def reduceWalls(self):
        a = self.walls[:]
        for i in a:
            self.walls.remove(i)
            new = False
            print("")
            print("I")
            i.p()
            print(i.walldir)
            for j in self.walls:
                print("j")
                j.p()
                print(j.walldir)
                if i.walldir == j.walldir:
                    if (i.x1,i.y1) == (j.x0,j.y0):
                        self.walls.remove(j)
                        self.walls.append(Wall(i.x0,i.y0,j.x1,j.y1))
                        new = True
                    elif (i.x1,i.y1) == (j.x1,j.y1):
                        self.walls.remove(j)
                        self.walls.append(Wall(i.x0,i.y0,j.x0,j.y0))
                        new = True
            if not new:
                self.walls.append(Wall(i.x0,i.y0,i.x1,i.y1))
        print(len(self.walls))

    def print_map(self):
        a = [["*"for i in range(6*int((self.size+1)))]for j in range(6*int(self.size+1))]
        for i in self.knots:
            x = 4+int(self.size-i.pos[1]-0.5)*3
            y = 4+int(self.size+i.pos[0]-0.5)*3
            a[x][y] = " "
            a[x][y] = str(len(i.getNeightbor()))
            if i.is_start:
                a[x][y] = "s"
            if i.is_goal:
                a[x][y] = "g"

            a[x+1][y+1] = " " 
            a[x+1][y-1] = " " 
            a[x-1][y+1] = " " 
            a[x-1][y-1] = " " 

            # North
            if i.north == None:
                a[x-1][y+1] = "-" 
                a[x-1][y]   = "-"
                a[x-1][y-1] = "-"
            else:
                a[x-1][y]   = " " 
            
            #East
            if i.east == None:
                a[x+1][y+1] = "|"
                a[x][y+1]   = "|"
                a[x-1][y+1] = "|"
            else:
                a[x][y+1]   = " "
            
            #South
            if i.south == None:
                a[x+1][y+1] = "-"
                a[x+1][y]   = "-"
                a[x+1][y-1] = "-"
            else:
                a[x+1][y]   = " "
            
            #West
            if i.west == None:
                a[x+1][y-1] = "|"
                a[x][y-1]   = "|"
                a[x-1][y-1] = "|"
            else:
                a[x][y-1]   = " "

        self.printmat(a)

    def printmat(self,a):
        for i in range(len(a)):
            s = ""
            for j in range(len(a[0])):
                s += str(a[i][j][0])
            print(s)

class Walker(object):

    def __init__(self, angle, start_knot, knots):
        self.cur = (0.5,0.5)
        self.start = start_knot
        self.path = list()
        self.visited = list()
        self.pos = (0.5, 0.5)
        self.angle = angle
        self.knots = knots
        self.goal = self.findgoal()
        self.path.extend(self.findpath(start_knot))
        print(self.path)

    def move(self):
        if self.getdist(self.pos,self.goal.pos) > 0.05:
            if self.getdist(self.pos,self.path[0]) < 0.05:
                self.pos = self.path[0]
                self.cur = self.path.pop(0)
            dif = (self.cur[0]-self.path[0][0],self.cur[1]-self.path[0][1])
            if dif[0] != 0:
                if dif[0] > 0:
                    nextangle=math.pi
                else:
                    nextangle=0.0
            else:
                if dif[1] > 0:
                    nextangle=math.pi*3.0/2.0
                else:
                    nextangle=math.pi/2.0
            adif = clampangle(nextangle-self.angle)
            if math.fabs(adif) > 0.01:
                self.angle = self.angle + adif*0.01
            else:
                self.angle= nextangle
                self.pos = (self.pos[0]-dif[0]*0.003,self.pos[1]-dif[1]*0.003)
            return True

        return False
               
    def findgoal(self):
        goal = None
        for i in self.knots:
            if i.is_goal:
                goal = i
        return goal

    def findpath(self,knot):
        if self.visited.count(knot.pos) > 0:
            return list()
        path = list()
        self.visited.append(knot.pos)
        path.append(knot.pos)
        knot.gen(self.start,SEED,SIZE)
        for i in knot.getNeightbor():
            if self.visited.count(i.pos) == 0:
                path.extend(self.findpath(i))
                path.append(knot.pos)
        return path

    def getdist(self,(ax,ay),(bx,by)):
        distx = ax - bx
        disty = ay - by
        return math.sqrt(distx**2 + disty**2)
    
    def getpos(self):
        return self.pos[0], self.pos[1] ,self.angle

#	def step(self):
#		self.state += PRIMITIVEWALK_STEP_SIZE
#		if self.state>=1.0:
#			self.state-=1.0

#	def getpos(self):
#		s = self.state*4.0
#		if s<1.0:
#			return ( 2.5 , 1.5+4.0*s , math.pi*0.5 )
#		s-=1.0
#		if s<1.0:
#			return ( 2.5 , 5.5 , math.pi*(0.5+s) )
#		s-=1.0
#		if s<1.0:
#			return ( 2.5 , 5.5-4.0*s , math.pi*1.5 )
#		s-=1.0
#		return ( 2.5 , 1.5 , math.pi*(1.5-s) )


WALKSPEED = 0.1
ROTSPEED = 0.1
WALK_DECAY = 0.1
ROT_DECAY = 0.1

class InteractiveWalker(object):

    def __init__(self, io, start_knot, list_of_walls):
        self.curknot = start_knot
        self.walllist = list_of_walls
#        self.visited = list()
        self.pos = tuple(self.curknot.pos)
        self.angle = 0.0
        self.io = io
        self.vel = (0.0,0.0)
        self.rotspeed = 0.0
        self.idle = 0.0


    def move(self):
        dt = 1.0    # remove. make this an argument.
        inp = self.io.getch()
        if inp=="\x1b[D": # left
                self.rotspeed = 0.02
        if inp=="\x1b[C": # right
                self.rotspeed = -0.02
        self.angle = clampangle(self.angle+self.rotspeed*dt)

        self.idle = (self.idle+0.0025)%1.0

        _spd = 0.02  # speed of movement  ..... constant here??
        q1 = 0.2*dt     # factor for e^-x curve
        q0 = 1.0-q1   # use these as:  gradual_newval = (currentval*q0 + targetval*q1)
        if inp=="\x1b[A" or inp=="\x1b[B": # up or down
                newvel = ( math.cos(self.angle)*_spd , math.sin(self.angle)*_spd )
                if inp=="\x1b[B": # backward?
                        newvel = (newvel[0]*-0.5,newvel[1]*-0.5)
                # apply new speed instantly.
                self.vel = newvel
                # apply new speed gradually.
                #self.vel = ( self.vel[0]*q0+newvel[0]*q1 , self.vel[1]*q0+newvel[1]*q1 )

        # move according to speed vector
        newpos = ( self.pos[0]+self.vel[0]*dt , self.pos[1]+self.vel[1]*dt )

        self.pos = newpos
        #bestcp = None
        #bestd = 0.0
        for wl in self.walllist:
                cp = closepoint_point_line(newpos,(wl.x0,wl.y0),(wl.x1,wl.y1))
                poscor = correct_position(self.pos,cp,0.333)
                if poscor is not None:
                        self.pos = poscor
                        newpos = poscor
                        # todo: need to change speed-vector?
        #if bestcp:
        #        print (repr(bestcp))

        # damp speed and rotspeed
        q0 = (1.0-0.05*dt)  # factor for e^-x curve
        self.vel = (self.vel[0]*q0,self.vel[1]*q0)
        self.rotspeed = self.rotspeed * q0

        return True

    def findgoal(self):
    	return None

    def getpos(self):
        x,y = self.pos[0], self.pos[1]
        x += math.cos(self.idle*math.pi*2)*0.025
        y += math.sin(self.idle*math.pi*2)*0.025
        return x, y ,self.angle

""" from poitn 'pt', find closest point on line, return that. """
def closepoint_point_line(pt,lin0,lin1):
        d = (lin1[0]-lin0[0],lin1[1]-lin0[1])
        linlen = math.sqrt(d[0]*d[0]+d[1]*d[1])
        if linlen<1.0e-9:
                return lin0
        dn = (d[0]/linlen,d[1]/linlen)
        q = (pt[0]-lin0[0])*dn[0] + (pt[1]-lin0[1])*dn[1]  # point along length of line.
        q = min(linlen,max(0.0,q))
        return ( lin0[0]+q*dn[0] , lin0[1]+q*dn[1] )

""" correct a position to not get too close to point 'cp'. return correction vector or None. """
def correct_position(pos,cp,rad):
        d = (cp[0]-pos[0],cp[1]-pos[1])
        linlen = math.sqrt(d[0]*d[0]+d[1]*d[1])
        if linlen>=rad or linlen<1.0e-6:
                return None
        _scal = rad/linlen
        return (cp[0]-d[0]*_scal,cp[1]-d[1]*_scal)



""" clamp an angle to a value of -pi to pi, by adding/subtracting 2*pi. """
def clampangle(ang):
    if ang<-math.pi:
        ang += 2*math.pi
    elif ang>math.pi:
        ang -= 2*math.pi
    return ang

if __name__=="__main__":
    sys.exit(main(sys.argv[1:]))
