"""
mazemap

Structures and classes containing the actual game map.

"""

import math
import random


class World(object):
    """ This object represents the entire map (world), and links to all other items such as walls, items, monsters, ... """
    __slots__=("walls","cells","entities")

    def __init__(self):
        self.walls=list()      # list of Wall objects.
        self.cells=list()      # list of knot objects (square cells to move around in).
        self.entities=list()      # list of Entity objects (enemies, player, pickups, ...).

    def add_knots(self,knot,bAllLinked=True):
        """ Add knot to list. If bAllLinked is true, walk all connected. """
        s2 = set()   # set of knots to add.
        s2.add(knot)
        if bAllLinked:
            goon=True
            while goon:
                goon=False
                for knt in list(s2):
                    _addthese = list()
                    if knt.north is not None:
                        _addthese.append(knt.north)
                    if knt.south is not None:
                        _addthese.append(knt.south)
                    if knt.west is not None:
                        _addthese.append(knt.west)
                    if knt.east is not None:
                        _addthese.append(knt.east)
                    for _addthis in _addthese:
                        if _addthis in s2:
                            continue
                        s2.add(_addthis)
                        goon = True

        s = set(self.cells) # existing knots
        # now have set with allconnected knots.
        for _addthis in s2:
            if _addthis not in s:
                self.cells.append(_addthis)



    def add_wall(self,x0,y0,x1,y1):
        """ Helper function, creates a Wall() object and adds it to 'walls' list. """
        self.walls.append(Wall(x0,y0,x1,y1))

    def look_dir(self,startX,startY,dx,dy):
        """ calculate a 2d ray into some direction, find which wall was hit. Return 4-tuple wall,distance,side,entityhit """
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
        enthit = None
        # try all entities
        bestedist=-1.0
        bestehit=None
#        print "DEBUG:   (%.1f/%.1f)  (%.1f/%.1f)" % (self.entities[0].x,self.entities[0].y,self.entities[1].x,self.entities[1].y)
        for ent in self.entities:
            dist = ent.hit(startX,startY,dx,dy)
            if dist is None:
                continue
            if dist<bestedist or (bestehit is None):
                bestedist=dist
                bestehit=ent
        if bestehit is not None:
            if (besthit is None) or (bestedist<bestdist):
                enthit = (bestehit,bestedist)  # the entity hit.
        if besthit is None:
            return None, None, None, enthit
        return besthit,bestdist,bestside,enthit

ENTRAD=0.095

class Entity(object):
    __slots__ = ("world","x","y")

    def __init__(self,world,x0,y0):
        self.world = world
        self.x=x0
        self.y=y0
        if self not in world.entities:
            world.entities.append(self)

    def destroy(self):
        if self.world is not None:
            try:
                self.world.entities.remove(self)
            except ValueError:
                pass
        self.world = None


    def get_pos(self):
        return (self.x,self.y)

    def hit(self,startX,startY,dx,dy):
        """ See if a ray hits this entity. Return distance. distance is None if not hitting entity at all. """
        # start of ray if circle (self) were origin.
        global ENTRAD
        x0 = startX-self.x
        y0 = startY-self.y
        # calc cut line with circle.
        # put line into equation  R^2 = x^2 + y^2
        # solve R^2 = a*lmb^2 + b*lmb + c
        a = dx*dx+dy*dy
        b = 2.0*x0*dx+2.0*y0*dy
        c = x0*x0+y0*y0-ENTRAD*ENTRAD
        # solution is   ( -b +- sqrt(b*b-4ac) ) / 2a
        _rad = b*b-4.0*a*c
        if _rad<=0.0:
            return None   # does not hit.
        _sqrt = math.sqrt(_rad)
        _lmb1 = (-b+_sqrt) / (2.0*a)
        _lmb2 = (-b-_sqrt) / (2.0*a)
        # have two solutions. if one is greater than 0, and other is less, startpoint is inside. distance is zero.
        if _lmb1*_lmb2 < 0.0:
            return None
            return 0.0  # inside.
        # if both negative, hits are behind. not a hit.
        if _lmb1<0.0:
            return None   # behind end of ray.
        # both positive. distance is smaller one of them. Multiply with length if direction vector and have distance.
        _distance = min(_lmb1,_lmb2) * math.sqrt(dx*dx+dy*dy)
#        print ".........hit an ent..........."
        return _distance


    def step(self,dt):
        """ base method for tick, called one per game-tick. """
        pass



class Wall(object):
    """ Object representing one wall. Holds end-coordinates, a direction field (radians), and a color. """
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
        """ See if a ray hits this wall. Return (distance,bIsFront). distance is None if not hitting wall at all. """
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
        # Kreuzprodukt der Richtungsvektoren, um zu bestimmen, welche Seite der Wand. Nur Z Komponente davon.
        krz = rx*dy - ry*dx
        return lmb2,(krz>=0.0)


WO=1

class knot(object):
    """ A 'knot' represents a cell, a square tile of the map. It is linked with all neighbors (where there is not wall). """

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

