#!/usr/bin/env python

# program to play tetris on frozen-bottle setup using cursor-key input on terminal.


import socket
import time
import sys
import random
import argparse
import LedClientBase
import hex
import noncanon_input

DEFAULT_PORT = 8901

class brickdef(object):
	__slots__ = ('shape','colorindex')
	def __init__(self,shape,colorindex):
		self.shape = tuple(shape)
		self.colorindex = int(colorindex)

BRICK_BAR    = brickdef( ((-1,0),(0,0),(1,0)) , 1 )
BRICK_CURV   = brickdef( ((-1,0),(0,0),(1,1)) , 2 )
BRICK_DIAMOND= brickdef( ((-1,0),(0,0),(1,1),(0,1)) , 3 )
BRICK_CROOK  = brickdef( ((-1,0),(0,0),(1,0),(0,1)) , 4 )

all_brickdefs = (BRICK_BAR,BRICK_CURV,BRICK_DIAMOND,BRICK_CROOK)

colrgb = (
	"\x00\x00\x00","\xE0\x00\x00","\x00\xE0\x00","\x00\x00\xE0",
	"\xC0\xC0\x00","\xC0\xA0\x50","\x00\x00\x00","\x00\x00\x00",
	"\x00\x00\x00","\x00\x00\x00","\x00\x00\x00","\x00\x00\x00",
	"\x00\x00\x00","\x00\x00\x00","\xE0\xE0\xE0","\x60\x60\x60"
)

class brick(object):
	__slots__ = ('field','bdef','w','h','dir','slide_right')

	# transforms for the six rotations
	xforms = (hex.HexBuff.XFORM_UNITY,hex.HexBuff.XFORM_ROT60,hex.HexBuff.XFORM_ROT120,hex.HexBuff.XFORM_ROT180,hex.HexBuff.XFORM_ROT240,hex.HexBuff.XFORM_ROT300)

	def __init__(self,field,brickdf):
		if not isinstance(brickdf,brickdef) or not isinstance(field,hex.HexBuff):
			raise TypeError("need a hex.HexBuff and a brickdef")
		self.field = field
		self.bdef = brickdf
		self.w , self.h = self.find_center_of_top_row()
		self.dir = 0
		self.slide_right = True
		valid=False
		for h in xrange(self.h,-1,-1):
			if self.doesfit(self.w,h,self.xforms[self.dir]):
				self.h = h
				valid=True
				break
		if not valid:
			raise Exception("cannot place brick. all blocked.")

	def doesfit(self,w,h,xform):
		if w<0 or h<0 or w>=self.field.w or h>=self.field.h:
			return False
		mt = hex.HexBuff.transform_list_of_tuples(self.bdef.shape,xform)
		for dw,dh in mt:
			if self.field.get_wh(dw+w,dh+h)!=0:
				return False
		return True

	def slide_down(self,pref_dw=0):
		toRgt = self.slide_right
		if pref_dw<0:
			toRgt=False
		if pref_dw>0:
			toRgt=True
		# attempt to slide down, both dirs.
		dwl=(0,-1)
		if not toRgt:
			dwl=(-1,0)
		for dw in dwl:
			if self.doesfit(self.w+dw,self.h-1,self.xforms[self.dir]):
				self.h -= 1
				self.w += dw
				self.slide_right = (dw==0)
				return True
		return False

	def move_sideways(self,dw=1):
		if dw>=0:
			dw=1
		else:
			dw=-1
		self.slide_right = (dw>=0)
		if self.doesfit(self.w+dw,self.h,self.xforms[self.dir]):
			self.w += dw
			return True
		return False

	def try_rotate(self):
		# try to rotate. This might need to shift position to match.
		ddir = -1
		xform = self.xforms[(self.dir+6+ddir)%6]
		trypos = list()
		trypos.append((0,0))
		trypos.extend(hex.dir_wh)
		for dw,dh in trypos:
			if self.doesfit(self.w+dw,self.h,xform):
				self.w += dw
				self.h += dh
				self.dir = (self.dir+6+ddir)%6
				return True
		return False


	def render(self,add_colors=True):
		mt = hex.HexBuff.transform_list_of_tuples(self.bdef.shape,self.xforms[self.dir])
		col = self.bdef.colorindex
		if not add_colors:
			col = 0
		for dw,dh in mt:
			dw += self.w
			dh += self.h
			if self.field.get_wh(dw,dh) is not None:
				self.field.set_wh(dw,dh,col)

	def find_center_of_top_row(self):
		for h in xrange(self.field.h-1,-1,-1):
			mn,mx = 4096,-4096
			for w in xrange(self.field.w):
				if self.field.get_wh(w,h) is not None:
					mn = min(mn,w)
					mx = max(mx,w)
			if mn<=mx:
				return (mn+mx)>>1,h
		raise Exception("no valid spaces in field???")


class game(object):
	__slots__ = ('field','brk','state','delayp','delay','fulllines','score','next_bdef')
	# states: 0=normal, 1=flash lines, 2=gameover
	def __init__(self,field):
		if not isinstance(field,hex.HexBuff):
			raise TypeError("need a hex.HexBuff")
		self.field = field
		self.brk = None
		self.state = 0
		self.delayp = 6000
		self.delay = 0
		self.fulllines = None
		self.score = 0
		self.next_bdef = self.pickbrick()
		for x in xrange(1,14,1):
			self.field.set_wh(x,1,1)
		for x in xrange(2,13,1):
			self.field.set_wh(x,2,2)

	def reset(self):
		self.delayp = 6000
                self.score = 0

	def pickbrick(self):
		return all_brickdefs[random.randint(0,len(all_brickdefs)-1)]

	def step(self,userinput=None):
		if (userinput is not None) and not isinstance(userinput,basestring):
			raise TypeError("userinput should be string.")
		if self.state==0:
			self.step0(userinput)
		elif self.state==1:
			self.step1(userinput)
		elif self.state==2:
			self.step2(userinput)
		elif self.state==3:
			self.step3(userinput)
		else:
			raise Exception("invalid state "+repr(self.state))

	def step0(self,inp):
		# normal run.
		if self.brk is None:
			try:
				self.brk = brick(self.field,self.next_bdef)
				self.brk.render(True)
				self.next_bdef = self.pickbrick()
				#print "added new brick"
			except Exception,ex:
				# cannot spawn new brick. game lost.
				self.state=2
				return
		# proc user-input
		if inp=="\x1b[D":
			self.brk.render(False)
			self.brk.move_sideways(-1)
			self.brk.render(True)
		if inp=="\x1b[C":
			self.brk.render(False)
			self.brk.move_sideways(1)
			self.brk.render(True)
		if inp=="\x1b[A":
			self.brk.render(False)
			self.brk.try_rotate()
			self.brk.render(True)
		if inp=="\x1b[B":
			self.delay=0

		# process auto-movedown
		self.delay-=1000
		if self.delay<=0:
			self.delay += self.delayp
			self.brk.render(False)
			res = self.brk.slide_down(0)
			self.brk.render(True)
			if not res:
				# not ok. is landed.
				# erase brick. will have new one next tick.
				self.brk = None
				# check if any lines are full
				self.fulllines = find_full_lines(self.field)
				if len(self.fulllines)>0:
					self.delay=3000
					self.state = 1
					fl = len(self.fulllines)
					self.score += fl+fl
					self.delayp *= 0.98
					highlight_lines(self.field,self.fulllines)
					return

	def step1(self,inp):
		# flash finished lines
		self.delay-=1000
		if self.delay>0:
			return
		move_down_rest(self.field,self.fulllines)
		self.delay = self.delayp

		self.state = 0

	def step2(self,inp):
		# game over
		if inp in (" ","\n","\r"):
			self.delay=0
			clearboard(self.field, self)
			self.state=0

	def step3(self,inp):
		# doh?
		pass




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

	# start non-canonical input
	tio = noncanon_input.cio()

	# connect to socket
	if not LedClientBase.connect(address,port):
		return 1

	t = 0.0

	# build array matrix.
	field = LedClientBase.get_matching_HexBuff(0,1)

	brk = brick(field,BRICK_CURV)

	tickdown_time = 2
	next_tickdown = tickdown_time

	gam = game(field)

	for i in xrange(0x7FFF0000):

		# do game.
		c=None
		while True:
			cc = tio.getch()
			if cc is None:
				break
			c=cc
		gam.step(c)

		# convert to color-LED-string
		lin = list()
		for j in xrange(LedClientBase.NUMLEDS):
			(xx,yy) = LedClientBase.seq_2_pos(j)
			colidx = field.get_xy(xx,yy)
			if colidx is None:
				colidx = 15
			lin.append(colrgb[colidx])

		# build scoreline
		_s = gam.score
		_s = "".join(colrgb[15*((_s>>b)&1)] for b in xrange(12))
		_s = colrgb[gam.next_bdef.colorindex] + _s
		_s = mix_col_liness(_s,"".join(lin[-13:]),2,1)
		del lin[-13:]
		lin.append(_s)

		#send
		LedClientBase.send("".join(lin))

		#loop-delay
		time.sleep(0.1)
		t += 0.100

	LedClientBase.closedown()

	return 0


def find_full_lines(field):
	res = list()
	for h in xrange(field.h):
		bm=0
		for w in xrange(field.w):
			c = field.get_wh(w,h)
			if c is not None:
				if c==0:
					bm |= 1
				else:
					bm |= 2
		if bm==2:	# only full spaces (no empty, and at least one full)
			res.append(h)
	return res

def highlight_lines(field,lines):
	for h in lines:
		for w in xrange(field.w):
			if field.get_wh(w,h) is not None:
				field.set_wh(w,h,14)

def move_down_rest(field,fulllines):
	# make mapping-list to map new lines from old.
	maph = range(field.h)
	rem = fulllines[:]
	rem.sort()
	rem.reverse()
	for h in rem:
		del maph[h]
	while len(maph)<field.h:
		maph.append(-1)
	# Oh Dreck. Wie runterschieben?? Zeilen sind nicht gleichlang...
	for h in xrange(field.h):
		from_h = maph[h]
		if from_h<0:	# clear line
			for w in xrange(field.w):
				if field.get_wh(w,h) is not None:
					field.set_wh(w,h,0)
		elif from_h!=h:
			# copy from [from_h]
			for w in xrange(field.w):
				if field.get_wh(w,h) is not None:
					val = field.get_wh(w,from_h)
					if val is None:
						val=field.get_wh(w+1,from_h)
						if val is None:
							val = 0
					field.set_wh(w,h,val)

def mix_col_liness(lin1,lin2,fac1,fac2):
	if len(lin1)!=len(lin2) or (len(lin1)%3)!=0:
		raise ValueError("need two strings of same length, multiple of 3")
	if (not isinstance(fac1,int)) or (not isinstance(fac2,int)) or fac1<1 or fac2<1:
		raise ValueError("bad factors. need integers, >=1. have "+repr((fac1,fac2)))
	sm = fac1+fac2
	res = list()
	for i in xrange(len(lin1)/3):
		p1=lin1[3*i:3*i+3]
		p2=lin2[3*i:3*i+3]
		res.append( chr((ord(p1[0])*fac1+ord(p2[0])*fac2)//sm) + chr((ord(p1[1])*fac1+ord(p2[1])*fac2)//sm) + chr((ord(p1[2])*fac1+ord(p2[2])*fac2)//sm) )
	return "".join(res)

def clearboard(field,game):
	game.reset()
	for h in xrange(field.h):
		for w in xrange(field.w):
			if field.get_wh(w,h) is not None:
				field.set_wh(w,h,0)


if __name__=="__main__":
	sys.exit(main(sys.argv[1:]))
