#!/usr/bin/env python

# non-canonical input using python.
# for some reason, python select.select() incorrectly reports no input 
# when the remainder of an escape sequence IS available.
# so we poll...

import atexit
import os
import time
import sys
if os.name == 'posix':
	#import select  # select does not work on escape-codes in input.
	import termios
elif os.name == 'nt':
	import msvcrt
else:
	raise Exception("os variant %s not supported"%repr(os.name))

CIO_STARTED = False

class cio(object):
	"""terminal-IO class for using non-canonical input

	Use getch() method to poll input. call is always non-blocking.
	If special chars or escape-codes are received, they are returned
	as one string in one call.
	For example, if user hits cursor-right, result is "\x1b[C".
	"""
	__slots__=('buf','posix','fh_ocfg','running')
	_winmap = { # mapping table for windows input >> posix input.
		"\r":"\n" ,
		"\xe0H":"\x1b[A" , "\xe0P":"\x1b[B" , "\xe0K":"\x1b[D" , "\xe0M":"\x1b[C" , # cur up/down/left/right
		"\xe0R":"\x1b[2~" , "\xe0S":"\x1b[3~" , "\xe0G":"\x1b[H" , "\xe0O":"\x1b[F" , "\xe0I":"\x1b[5~" , "\xe0Q":"\x1b[6~" , # ins/del/home/end/pgup/pgdn
		"\0;":"\x1b[[A" , "\0<":"\x1b[[B" , "\0=":"\x1b[[C" , "\0>":"\x1b[[D" ,   # F1 .. F4
		"\0?":"\x1b[[E" , "\0@":"\x1b[17~" , "\0A":"\x1b[18~" , "\0B":"\x1b[19~" ,   # F5 .. F8
		"\0C":"\x1b[20~" , "\0D":"\x1b[21~" , "\0\x85":"\x1b[23~" , "\0\x86":"\x1b[24~" ,   # F9 .. F12
	}
	def __init__(self):
		global CIO_STARTED
		if CIO_STARTED:
			raise Exception("cannot init cio twice")
		CIO_STARTED = True
		# stay compatible with gamecontroller
		self.running = True
		self.buf=''
		self.fh_ocfg=list()
		if os.name == 'posix':
			# for posix, need to set to non-canonical input.
			self.posix=True
			fh = sys.stdin.fileno()
			# if the following call fails, we are probably called with a stdin which is not a tty.
			ocfg = termios.tcgetattr(fh)
			cfg = termios.tcgetattr(fh)
			cfg[3] = cfg[3]&~termios.ICANON&~termios.ECHO
			#cfg[0] = cfg[0]&~termios.INLCR
			#cfg[1] = cfg[0]&~termios.OCRNL
			cfg[6][termios.VMIN] = 0
			cfg[6][termios.VTIME] = 0
			termios.tcsetattr(fh,termios.TCSAFLUSH,cfg)
			self.fh_ocfg.extend((fh,ocfg))
			atexit.register(stop_canon_input,self.fh_ocfg)
		elif os.name == 'nt':
			# for windows, don't need to configure the terminal.
			self.posix=False
		else:
			# know only posix and windows...
			raise Exception("os variant %s not supported"%repr(os.name))

	def __del__(self):
		if self.posix and (stop_canon_input is not None):
			stop_canon_input(self.fh_ocfg)
		CIO_STARTED = False

	def getch(self):
		c = self.getbyt()
		if c is None:
			return None
		#print self.getbyt_avail()
		if self.posix:
			# for posix, keep possing input until have a full, valid escape code.
			while self.is_escape_code(c)<0:
				n = self.getbyt()
				if n is None:
					break
				c = c+n
			if self.is_escape_code(c)<1:
				self.ungetbyt(c[1:])
				c = c[0]
		else:
			# for windows, get another byte if an extended symbol, then map.
			if c=='\xE0' or c=='\x00':
				n = self.getbyt()
				if n is not None:
					c = c+n
			# mapping from windows-dosbox inputs to posix-terminal inputs
			if c in self._winmap:
				c = self._winmap[c]
		return c

	def is_escape_code(self,st):
		""" check if is a posix terminal escape code. returns:
		   0 for no
		   1 for yes
		  -1 for unfinished yet. For example "\x1b["
		"""
		if len(st)<1 or st[0]!='\x1b':
			return 0
		if len(st)<2:
			return -1 # just an 'escape'.
		if st[1]!='[':
			return 0 # must be escape and [
		# now a number (or not)
		i = 2
		while i<len(st) and st[i].isdigit():
			i+=1
		# finally, a char in the range 64..126
		#print "...",repr(st),i
		if i>=len(st):
			return -1
		if ord(st[i])>=64 and ord(st[i])<=126:
			return 1
		return 0


	def getbyt(self):
		res = None
		if len(self.buf)>0:
			res = self.buf[0]
			self.buf = self.buf[1:]
		elif self.posix:
			nw = sys.stdin.read(32)
			if len(nw)>0:
				self.buf = nw[1:]
				res = nw[0]
		else:
			if msvcrt.kbhit():
				res = msvcrt.getch()
		return res

	def ungetbyt(self,b):
		self.buf = b+self.buf

	def puts(self,st):
		if self.posix:
			sys.stdout.write(st)
		else:
			for b in st:
				msvcrt.putch(b)

def stop_canon_input(fh_ocfg):
	if fh_ocfg is None:
		return
	args = fh_ocfg[:]
	del fh_ocfg[:]
	if len(args)>=2:
		termios.tcsetattr(args[0],termios.TCSAFLUSH,args[1])



# some tiny test program if started as standalone.

def test_main(args):
	tio = cio()
	for st in ("\x1b","\x1b[","\x1b[D"):
		print repr(st),tio.is_escape_code(st)
	tio.puts("line N>\n<N   line R>\r<R   line RN>\r\n<RN   line-printend")
	if False:
		for i in xrange(20):
			#if (i%5)==0:
			#	puts("\r")
			while True:
				d=tio.getch()
				if d is not None:
					break
				time.sleep(0.1)

			tio.puts(repr(d))

	if True:
		p = 5;w=30
		for i in xrange(100):
			while True:
				c=tio.getch()
				if c is None: break
				if c=='\x1b[D' and p>0: p-=1
				if c=='\x1b[C' and p+1<w: p+=1
			tio.puts((" "*p)+"*"+(" "*(w-1-p))+"\r")
			time.sleep(0.05)
	
	tio.puts("\r\n")
	del tio
	return 0


if __name__=="__main__":
	sys.exit(test_main(sys.argv[1:]))
