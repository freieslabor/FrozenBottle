#!/usr/bin/env python3
""" module with some stuff to work with hex-grid images """


class HexBuff(object):
	"""
		basically just a 2D array,
		with helper functions for hexes such as rotate and rot-paste and transform to x/y
		It uses two coordinate systems:
		w/h is a pair addressing the 2D array plain just like a 2D array.
		x/y is a pair transformed to a flat screen showing the hex-array. step-width is 2.
	"""
	__slots__ = ("data","w","h","ow","oh","defval")

	# some transforms. scribed X-forms are in XY (physical) plane,
	# matrix is to be applied to w,h pair. Pass these to blit()
	XFORM_UNITY = (1,0,0,1)
	XFORM_FLIP_X = (-1,1,0,1)
	XFORM_FLIP_Y = (1,-1,0,-1)
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
		self.defval = default_value
		dum = list()
		for i in range(w):
			dum.append(default_value)
		for i in range(h):
			self.data.append(dum[:])

	def fill_val(self,val):
		for H in range(self.h):
			datalin = self.data[H]
			for W in range(self.w):
				datalin[W]=val

	def set_wh(self,w,h,val):
		if w<0 or w>=self.w or h<0 or h>=self.h:
			return
		self.data[h][w] = val

	def get_wh(self,w,h):
		if w<0 or w>=self.w or h<0 or h>=self.h:
			return self.defval
		return self.data[h][w]

	def get_w(self):
		return self.w

	def get_h(self):
		return self.h

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
			xform = HexBuff.XFORM_UNITY
		# just plain, inefficient loops
		for H in range(image.h):
			datalin = image.data[H]
			oH = H-image.oh
			for W in range(image.w):
				val = datalin[W]
				if val is not None:
					oW = W-image.ow
					tw = xform[0]*oW + xform[1]*oH + self.ow + to_w
					th = xform[2]*oW + xform[3]*oH + self.oh + to_h
					self.set_wh(tw,th,val)

	@staticmethod
	def transform(w,h,xform):
		if xform is None:
			return (w,h)
		return ( xform[0]*w + xform[1]*h , xform[2]*w + xform[3]*h )

	@staticmethod
	def transform_list_of_tuples(ls,xform):
		if xform is None:
			return ls[:]
		res = list()
		for w,h in ls:
			res.append(( xform[0]*w + xform[1]*h , xform[2]*w + xform[3]*h ))
		return res

	def __iter__(self):
		return data.__iter__()

	def dbg_prnt(self,func_value2char):
		for h in range(self.h-1,-1,-1):
			ln = ' '.join(func_value2char(val) for val in self.data[h])
			ln = (" "*(self.h-1-h))+ln
			print(ln)



# array to use as direction vectors
dir_xy = ((2,0),(1,2),(-1,2),(-2,0),(-1,-2),(1,-2))
#dir_wh = ()  # not hard-coding but using transform function to remain consistent.
_dum = HexBuff(2,2)
dir_wh = tuple(_dum.xy2wh(dx,dy) for dx,dy in dir_xy)
del _dum
#print(repr(dir_xy))
#print(repr(dir_wh))


def read_hex_file(name,colors_as_float=False):
	f = open(name,"rb")
	fdat = f.read()
	f.close()
	fdat = fdat.decode('utf-8').split('\n')
	# remove comment lines and empty lines
	i = 0
	dat = False
	while i<len(fdat):
		l = fdat[i].strip()
		if l=='DATA': dat=True
		if (l=="" and not dat) or l.startswith('#'):
			del fdat[i]
			continue
		i+=1
	# first line must be 'HEX', followed by name
	if len(fdat)<1:
		raise ValueError("no lines")
		return None
	l = fdat[0].strip();del fdat[0]
	if not l.startswith("HEX"):
		raise ValueError("does not start with 'HEX'")
		return None
	l = l[3:]
	name = l.strip()
	# next line is 'COLORS'
	if len(fdat)<1:
		raise ValueError("no more lines after first line")
		return None
	l = fdat[0].strip();del fdat[0]
	if l != "COLORS":
		raise ValueError("expected 'COLORS' after HEX line")
		return None
	# now a set of lines with one char on head, space, three values.
	colmap=dict()
	while len(fdat)>0:
		l = fdat[0].strip();
		if len(l)<3: break
		if not l[1].isspace(): break
		del fdat[0]
		c = l[0]
		if c in colmap:
			raise ValueError("duplicate color-line for %s"%(repr(c)))
			return None
		l = l[1:].strip().split(',')
		if len(l)!=3:
			raise ValueError("color-line must have group of three values, comma-seperated. found %s"%(repr(','.join(l))))
			return None
		try:
			l = list(int(p) for p in l)
			if max(l)>255 or min(l)<0:
				raise ValueError()
		except Exception:
			raise ValueError("cannot interpret values in color-line as integers 0..255.")
			return None
		if colors_as_float:
			l = list(float(v)/255.0 for v in l)
		#print("color %s: %s" % (repr(c),repr(l)))
		colmap[c] = tuple(l)
	# when done, need 'DATA'
	if len(fdat)<1:
		raise ValueError("no more lines after color-lines. Need 'DATA' section.")
		return None
	l = fdat[0].strip();del fdat[0]
	if l != "DATA":
		raise ValueError("expected 'DATA' after colors section")
		return None
	# drop empty lines after 'DATA'
	while len(fdat)>0 and fdat[0].rstrip()=="":
		del fdat[0]
	# drop empty lines from end
	while len(fdat)>0 and fdat[-1].rstrip()=="":
		del fdat[-1]
	if len(fdat)<1:
		raise ValueError("DATA section empty")
		return None
	res = dict()
	y=2*(len(fdat)-1)
	for l in fdat:
		l = l.rstrip()
		for i in range(len(l)):
			c = l[i]
			if c.isspace():
				continue
			if c=='.':
				res[(i,y)] = None
				continue
			if c not in colmap:
				raise ValueError("using undefined item %s in data."%(repr(c)))
				return None
			res[(i,y)]=colmap[c]
		y-=2
	return res



# not to be started as a standalone program
if __name__=="__main__":
	import sys
	sys.exit(main(sys.argv[1:]))
