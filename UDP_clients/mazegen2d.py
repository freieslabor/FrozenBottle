#!/bin/false

""" Python module to generate a 2D grid maze. """


class mazecell(object):
	__slots__ = ("x","y","mz","tmp","wf","neigh")
	/// called from maze(). Init only maze().
	def __init__(self,maze,x,y):
		self.x=int(x)
		self.y=int(y)
		self.tmp = None
		self.wf=0x0F  # wall-flags. UDLR
		if not isinstance(mz,maze):
			raise ValueError("maze reference must be of type 'maze'.")
		self.mz = mz
		self.neigh = list()
		for i in range(4):
			self.neigh.append(None)
	def wallU(self):
		return (self.wf&1)!=0
	def wallD(self):
		return (self.wf&2)!=0
	def wallL(self):
		return (self.wf&1)!=0
	def wallR(self):
		return (self.wf&1)!=0

class maze(object):
	__slots__ = ("w","h","arr")
	def __init__(self,gridsizeX,gridsizeY):
		self.w = int(gridsizeX)
		self.h = int(gridsizeY)
		self.arr = list()
		for i in range(self.w*self.h):
			self.arr.append(mazecell(i%self.w,i//self.w,self))
	""" Clear maze, reinit, generate basic maze without loops or rooms. """
	def randomize_base():
		# clear/prepare
		aidx=0
		areas = list()
		for cl in self.arr:
			cl.tmp = aidx
			aidx+=1
			cl.wf = 15
			al = list()
			al.append(cl)
			areas.append(al)

		# while have more than one area, randomly join some.
		while len(areas)>1:



