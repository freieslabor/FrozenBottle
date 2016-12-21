#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# random-maze in the frozen-bottle


import argparse
import math
import random
import sys
import time
import LedClientBase
import hex

DEFAULT_PORT = 8901


class walker(object):
	__slots__ = ('maze','color','w','h','path','pi')
	def __init__(self,mz):
		self.maze = mz
		self.w,self.h = pick_a_space(self.maze)
		self.color = "\x77\x99\x44"
		self.path = None
		self.pi = 0

	def step(self):
		if self.path is None or self.pi >= len(self.path):
			tw,th = pick_a_space(self.maze)
			if tw is not None:
				self.path = findpath(self.maze,self.w,self.h,tw,th)
			self.pi = 0
		if self.path is not None and self.pi < len(self.path):
			self.w,self.h = self.path[self.pi]
			self.pi = self.pi+1


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

	# create, matching to frozen-bottle
	mz = LedClientBase.get_matching_HexBuff(-1,0)

	random.seed(2)
	grow(mz)


	t = 0.0

	colmap = (
		"\xDD\x44\x11",
		"\x00\x00\x00","\x00\xAA\x00","\x00\x00\xAA","\x55\x33\x00"
	)

	walkers = list()
	for i in xrange(4):
		walkers.append(walker(mz))

	for i in xrange(0x7FFF0000):

		for w in walkers:
			w.step()  # They're coming...

		# show walkers in map
		for w in walkers:
			mz.set_wh(w.w,w.h,2)
		# make color-data for map
		lin = list()
		for j in xrange(LedClientBase.NUMLEDS):
			(xx,yy) = LedClientBase.seq_2_pos(j)
			val = mz.get_xy(xx,yy)
			val = max(min(val,3),-1)

			lin.append(colmap[val+1])
		# hide walkers in map
		for w in walkers:
			mz.set_wh(w.w,w.h,0)
		# send to strip
		LedClientBase.send("".join(lin))

		time.sleep(0.100)
		t += 0.100

	LedClientBase.closedown()

	return 0


def val2char(val):
	mapp = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+*=/&%$§!\";:"
	if val is None: return " "
	if val<0: return '-'
	return mapp[val%len(mapp)]

def grow(mz):
	dirs = hex.dir_wh
	tries=0
	idx=0
	numgrp=0
	_dbg = True
	mz.dbg_prnt(val2char)
	while tries<1000:
		tries += 1
		w = random.randint(0,mz.w+1)
		h = random.randint(0,mz.h+1)
		v = mz.get_wh(w,h)
		if v != -1:
			continue
		nb = list()
		for i in xrange(6):
			dw,dh = dirs[i]
			vv = mz.get_wh(w+dw,h+dh)
			if (vv is None) or vv<0:
				continue
			nb.append((vv,i,dw,dh))
		if len(nb)<=0:
			# no groups as neighbors. start new group.
			mz.set_wh(w,h,idx)
			idx += 1
			numgrp += 1
			if _dbg: print "DBG: start new group #%d at (%d/%d)"%(idx-1,w,h)
		elif len(nb)==1:
			# one space of a group. add to group.
			mz.set_wh(w,h,nb[0][0])
			if _dbg: print "DBG: extend group #%d at (%d/%d)"%(nb[0][0],w,h)
		else:
			# multiple spaces of groups.
			nb.sort()
			if nb[0][0]==nb[-1][0]:
				# all same group
				# see if we would create a circle.
				bits = 0
				for i in xrange(len(nb)):
					bits = bits | (1<<nb[i][1])
				if bits not in iscirclemap:
					continue # neighbors not adjacent. would create a ring.
				# choose random to not add one.
				_r = random.randint(0,len(nb)-1)
				if _r > 0:
					continue
				# add anyway.
				if _dbg: print "DBG: extend group #%d (wide) at (%d/%d)"%(nb[0][0],w,h)
				mz.set_wh(w,h,nb[0][0])
			else:
				#multiple groups. Add space and join groups.
				mz.set_wh(w,h,nb[0][0])
				for i in xrange(1,len(nb)):
					while i<len(nb) and nb[i-1][0]==nb[i][0]:
						del nb[i]
				for og,di,dw,dh in nb[1:]:
					if _dbg: print "DBG: join group #%d(%d/%d) with #%d(%d/%d) at (%d/%d)"%(nb[0][0],w,h,og,w+dw,h+dh,w,h)
					connect(mz,w,h,w+dw,h+dh,_dbg)
					numgrp -= 1
					#mz.dbg_prnt(val2char)
	mz.dbg_prnt(val2char)
	return numgrp==1



def connect(mz,w1,h1,w2,h2,_dbg=False):
	g1 = mz.get_wh(w1,h1)
	g2 = mz.get_wh(w2,h2)
	if (g1 is None) or (g2 is None) or (g1==g2) or (g1<0) or (g2<0):
		raise ValueError()
	# scanning all. a grow-function would be faster??
	rn=0
	for h in xrange(mz.h):
		for w in xrange(mz.w):
			if mz.get_wh(w,h)==g2:
				mz.set_wh(w,h,g1)
				rn += 1
	if _dbg: print "DBG:  connected #%d to #%d (renamed %d cells)"%(g1,g2,rn)



def pick_a_space(mz):
	for i in xrange(0x1000):
		w = random.randint(0,mz.w-1)
		h = random.randint(0,mz.h-1)
		c = mz_costfunc(mz.get_wh(w,h))
		if c is not None and c<1000:
			return w,h
	return None,None


def mz_costfunc(val):
	if (val is None) or (val<0):
		return None
	return 1

def findpath(mz,w1,h1,w2,h2):
	mm = findgrow(mz,w2,h2,mz_costfunc)
	if mm[h1][w1] is None:
		return None
	res = list()
	w,h = w1,h1
	res.append((w,h))
	while w!=w2 or h!=h2:
		di = mm[h][w]
		if di is None:
			return None
		di = ((di&7)+3)%6
		dw,dh = hex.dir_wh[di]
		w += dw
		h += dh
		res.append((w,h))
	return res


def findgrow(mz,start_w0,start_h0,costfunc_val2cost,limit=0x0FFFFFFF):
	# prepare output list
	_t = [None]*mz.w
	res = list()
	for h in xrange(mz.h):
		res.append(_t[:])
	del _t
	if start_w0<0 or start_h0<0 or start_w0>=mz.w or start_h0>=mz.h:
		raise ValueError("seed outside map (%d/%d)."%(start_w0,start_h0))
	# seed
	gl1=list()
	gl2=list()
	res[start_h0][start_w0]=0
	gl1.append((start_w0,start_h0))
	while len(gl1)>0:
		for w,h in gl1:
			c = res[h][w]>>3
			for di in xrange(6):
				dw,dh = hex.dir_wh[di]
				cost = costfunc_val2cost(mz.get_wh(w+dw,h+dh))
				if (cost is None):
					continue	# not reachable
				tc = res[h+dh][w+dw]
				if ((tc is not None)and(c+cost>=(tc>>3))) or (c+cost)>limit:
					continue	# not an improvement or over limit
				# is better. add to gl2
				gl2.append((w+dw,h+dh))
				res[h+dh][w+dw] = ((c+cost)<<3)+di
		# swap lists
		del gl1[:]
		_t = gl2;gl2=gl1;gl1=_t
	return res



# create the circlemap. it is for testing if the sequence of indices 0..5 is all adjacent (circular around the 5..0 point)
iscirclemap = list()
for i in xrange(0x40):
	if i==0:
		iscirclemap.append(False)
		continue
	if i==63:
		iscirclemap.append(True)
		continue
	#rotate so bit #0 is set and bit #5 is clear
	while (i&0x21)!=1:
		i = (i>>1) + (((i&1)<<5))
	iscirclemap.append( i&(i+1) == 0 )


if __name__=="__main__":
	sys.exit(main(sys.argv[1:]))
