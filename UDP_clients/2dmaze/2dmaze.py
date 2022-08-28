#!/usr/bin/env python3

import os.path
import sys
# Add parent directory to import search path
sys.path.append(os.path.dirname(os.path.dirname( os.path.abspath(__file__) )))


import argparse
import math
import sys
import time
import LedClientBase
import random
import noncanon_input
import maze


DEFAULT_PORT = 8901

TIMESTEP = 0.02

PRIMITIVEWALK_STEP_SIZE = 0.005

SIZE = 2

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
    gen.print_map()     # debug show map as ascii.
    grid.cells = knots
    io = noncanon_input.cio()

    # dummy entities.
#    maze.Entity(grid,1.3,0.1)
#    maze.Entity(grid,-0.1,1.3)
#    maze.Entity(grid,-1.3,-0.1)
#    maze.Entity(grid,0.1,-1.3)

    # create walker. either the interactive, or the automatic.

    w = Walker(grid, math.pi, gen.start, knots)
    w = InteractiveWalker(grid, io, gen.start, gen.walls)

    v = Viewer(resX=27,resY=28,fow=2.5)
    gametime = 0.0
    nextspawn = 2.0
    while True:

        # move all entities.
        for ent in grid.entities:
            ent.step(TIMESTEP)
        if gametime>=nextspawn:
            nextspawn += 2.5
            Walker(grid, math.pi, gen.start, knots)
            print("DEBUG: spawned new walker. number of entities: "+repr(len(grid.entities)))
        gametime = gametime + TIMESTEP


        x,y,r = w.getpos()
        #v.new_pos( 0.5,1.5 , math.pi*0.500*(i/20.0) )
        #v.new_pos( 0.5,1.01+i/4.0 , math.pi*0.50 )
        v.new_pos( x,y,r )

        va = v.view(grid)


        # convert to FrozenBottle LED sequence
        seq = list()
        for i in xrange(LedClientBase.NUMLEDS):
            x,y = LedClientBase.seq_2_pos(i)
            col_tub = [0,0,0,0]
            for j in range(4):
                sub_x = x #+ j%2
                sub_y = y + j//2
                if sub_x>=0 and sub_y>=0 and sub_x<v.resX and sub_y<v.resY:
                    col_tub[j] = v.gfxmatrix[sub_x+v.resX*sub_y]
            col = meancol_of_4(col_tub)
            val1, val2, val3 = col&255, (col>>8)&255, (col>>16)&255
            seq.append(LedClientBase.rgbF_2_bytes((val1/100, val2/100, val3/100)))

        LedClientBase.send(b"".join(seq))
        w.move()

        time.sleep(TIMESTEP)

    LedClientBase.closedown()

    return 0

def meancol_of_4(col_tup):
        sumr,sumg,sumb=0,0,0
        for col in col_tup:
                sumr += col&255
                sumg += (col>>8)&255
                sumb += (col>>16)&255
        sumr //= 4
        sumg //= 4
        sumb //= 4
        return sumr+(sumg<<8)+(sumb<<16)


WALL_H = 1.0
VIS_H = 0.6    # eye height.

class Viewer(object):
    __slots__=("posX","posY","angle","fow","resX","resY","gfxmatrix","_wdd")
    def __init__(self,fow=math.pi/2.0,resX=28,resY=28):
        self.posX = 0.0
        self.posY = 0.0
        self.angle = 0.0
        self.fow = fow
        self.resX = resX
        self.resY = resY
        self.gfxmatrix = [0]*(self.resX*self.resY)
        # wdd variable is needed to transform distances to visual hight.
        # with of  orthogonal sampling edge. depends on fow.
        self._wdd = 0.5*math.sqrt( (math.cos(self.fow)-1.0)**2 + (math.sin(self.fow))**2 )

    def new_pos(self,x,y,angle=None):
        self.posX=x
        self.posY=y
        if angle is not None:
            self.angle = angle

    def view(self,grid):
        hits = self.view_calc_hits(grid)

        x = 0
        for (_dst,col,walldir,enthit) in hits:

            #zero-out the column
            for y in xrange(0,self.resY):
                self.gfxmatrix[x+self.resX*y] = 0


            if col is None:
                col = 0
                # have hit a wall here.

            if _dst is not None:
                h0 = self.transform_Y( _dst ,    0.0-VIS_H )
                h1 = self.transform_Y( _dst , WALL_H-VIS_H )

                # calc y-range
                y0 = int( self.resY * (0.5 + h0*0.5) + 0.5 )
                y1 = int( self.resY * (0.5 + h1*0.5) + 0.5 )
                y0 = max(0,y0)
                y1 = min(self.resY,y1)

                # fill in gfx buffer
                for y in xrange(y0,y1):
                    self.gfxmatrix[x+self.resX*y] = col

            if enthit is not None:
                _ent,_dist = enthit
                #if _ent.x == self.posX and _ent.y==self.posY:
                #    continue
#                y = int( self.resY * (0.5) + 0.5 )
#                if y>=0 and y<self.resY:
#                    self.gfxmatrix[x+self.resX*y] = 0xEEEEEE

                h0 = self.transform_Y( _dist ,    0.0-VIS_H )
                h1 = self.transform_Y( _dist ,    0.6-VIS_H )   # visual height of entities. constant here?

                # calc y-range
                y0 = int( self.resY * (0.5 + h0*0.5) + 0.5 )
                y1 = int( self.resY * (0.5 + h1*0.5) + 0.5 )
                y0 = max(0,y0)
                y1 = min(self.resY,y1)

                # fill in gfx buffer
                for y in xrange(y0,y1):
                    self.gfxmatrix[x+self.resX*y] = 0xEEEEEE


            x+=1



    def view_calc_hits(self,grid):
        # calc the 2D view.
        # returns a list of 4-tuples. vis-height,color,wall-direction,(entityhit,entitydistance)
        res = list()
        # view-vector
        vx = math.cos(self.angle)
        vy = math.sin(self.angle)
        # orthogonal step, to be added multiple times to the view-vector.
        qsx = -vy
        qsy = vx
        #print("DEBUG: _wdd = %f"%self._wdd)
        for i in xrange(self.resX):
            q = i/float(self.resX-1) - 0.5  # -1 .. 1
            q = -q ## lieber von links nach rechts.
            # sample view
            wall,dist,side,enthit = grid.look_dir( self.posX , self.posY , vx+qsx*self._wdd*q , vy+qsy*self._wdd*q )
            #print(wall,dist)
            if wall:
                # see a wall
                vis_height = WALL_H / (dist*self._wdd)

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
                dist = None
            res.append((dist,color,walldir,enthit))
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

    def transform_Y(self,distance,y_3d):
        """ transform vertical coordinate to screen coordinate. Result in range -1 .. 1 is in screen height. """
        return y_3d / (distance*self._wdd)



class generator(object):

    def __init__(self,size,seed):
        self.start = maze.knot(0.5,0.5,is_start=True)
        self.size = 5
        self.knots = list()
        self.size = size
        self.walls = list()
        self.grid = maze.World()
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
            print(i.p())
        #self.reduceWalls()
        self.grid.walls = self.walls
        for i in self.walls:
            print(i.p())
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

class Walker(maze.Entity):

    def __init__(self, world, angle, start_knot, knots):
        maze.Entity.__init__(self,world,start_knot.pos[0],start_knot.pos[1])
        self.cur = (0.5,0.5)
        self.start = start_knot
        self.path = list()
        self.visited = list()
        self.pos = (0.5, 0.5)
        self.angle = angle
        self.knots = knots
        self.goal = self.findgoal()
        self.path.extend(self.findpath(start_knot))
        self.done = False
        print(self.path)

    def step(self,dt):
        if not self.move():
            self.destroy()
            return
        self.x,self.y = self.pos

    def move(self):
        if self.getdist(self.pos,self.goal.pos) > 0.05:
            if self.getdist(self.pos,self.path[0]) < 0.05:
                self.pos = self.path[0]
                self.cur = self.path.pop(0)
                print("now at "+repr(self.pos))
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
                self.angle = self.angle + adif*0.1   # rotation speed here.
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

    def getdist(self, a, b):
        ax, ay = a
        bx, by = b
        distx = ax - bx
        disty = ay - by
        return math.sqrt(distx**2 + disty**2)

    def getpos(self):
        return self.pos[0], self.pos[1] ,self.angle

#    def step(self):
#        self.state += PRIMITIVEWALK_STEP_SIZE
#        if self.state>=1.0:
#            self.state-=1.0

#    def getpos(self):
#        s = self.state*4.0
#        if s<1.0:
#            return ( 2.5 , 1.5+4.0*s , math.pi*0.5 )
#        s-=1.0
#        if s<1.0:
#            return ( 2.5 , 5.5 , math.pi*(0.5+s) )
#        s-=1.0
#        if s<1.0:
#            return ( 2.5 , 5.5-4.0*s , math.pi*1.5 )
#        s-=1.0
#        return ( 2.5 , 1.5 , math.pi*(1.5-s) )


WALKSPEED = 0.1
ROTSPEED = 0.1
WALK_DECAY = 0.1
ROT_DECAY = 0.1

class InteractiveWalker(maze.Entity):

    def __init__(self, world, io, start_knot, list_of_walls):
        maze.Entity.__init__(self,world,start_knot.pos[0],start_knot.pos[1])
        self.curknot = start_knot
        self.walllist = list_of_walls
#        self.visited = list()
        self.pos = tuple(self.curknot.pos)
        self.angle = 0.0
        self.io = io
        self.vel = (0.0,0.0)
        self.rotspeed = 0.0
        self.idle = 0.0


    def step(self,dt):
        self.move()

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
        #        print(repr(bestcp))

        # damp speed and rotspeed
        q0 = (1.0-0.05*dt)  # factor for e^-x curve
        self.vel = (self.vel[0]*q0,self.vel[1]*q0)
        self.rotspeed = self.rotspeed * q0

        self.x,self.y = self.pos
        return True

    def findgoal(self):
        return None

    def getpos(self):
        x,y = self.pos[0], self.pos[1]
        #x += math.cos(self.idle*math.pi*2)*0.025
        #y += math.sin(self.idle*math.pi*2)*0.025
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

