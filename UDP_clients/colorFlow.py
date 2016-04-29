#!/usr/bin/env python

# program to send some blinking to UDP for the flozen-bottle setup.


import socket
import time
import math
import sys

ADDRESS = "127.0.0.1"
#ADDRESS = "172.17.0.4"
#ADDRESS = "172.17.0.110"
ADDRESS = "192.168.7.7"
DEFAULT_PORT = 8901


NUMLEDS = 95
LEN_FIRST_ROW = 14




def main(args):

	(aa,ao) = parse_args( args , () , ('p') )

	if aa is None:
		return 1

	port = DEFAULT_PORT

	if 'p' in ao:
		port = int(ao['p'])
		if port<=0 or port==0xFFFF:
			sys.stderr.write("bad port number %u\n"%port)
			return 1


	s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	addr = (ADDRESS,port)

	print "sending to UDP %s:%u" % (ADDRESS,port)

	t = 0.0

	for i in xrange(0x7FFF0000):

		lin = list()
		for j in xrange(NUMLEDS):
			(xx,yy) = seq_2_pos(j)
			rgb_tuple = color_calc_func_1(i,j,xx,yy)
#			rgb_tuple = color_calc_func_2(i,j,xx,yy)


			xxx = list(rgb_tuple)
			xxx.sort()
		###	rgb_tuple = (xxx[1],xxx[2],xxx[0])


			lin.append(rgbF_2_bytes(rgb_tuple))
		s.sendto("".join(lin),addr)

		time.sleep(0.017)
		t += 0.017

	s.close()

	return 0


def hsv2rgb_float(h,s,v):
	if h<0.0: h=0.0
	if h>1.0: h=1.0
	if s<0.0: s=0.0
	if s>1.0: s=1.0
	if v<0.0: v=0.0
	if v>1.0: v=1.0
	h = h*6.0
	if h<=3.0:
		if h<=1.0:
			r = 1.0;g=h;b=0.0
		elif h<=2.0:
			r = 2.0-h;g=1.0;b=0.0
		else:
			r = 0.0;g=1.0;b=h-2.0
	else:
		if h<=4.0:
			r = 0.0;g=4.0-h;b=1.0
		elif h<=5.0:
			r = h-4.0;g=0.0;b=1.0
		else:
			r = 1.0;g=0.0;b=6.0-h
	q = 1.0-s
	r = q+s*r
	g = q+s*g
	b = q+s*b
	return (v*r,v*g,v*b)


def rgbF_2_bytes(rgb):
	# pass in tuple
	r,g,b = rgb
	r = int(256.0*r)
	if r>255: r=255
	g = int(256.0*g)
	if g>255: g=255
	b = int(256.0*b)
	if b>255: b=255
	return chr(r)+chr(g)+chr(b)

def seq_2_pos(idx):
	dblRow = idx//(LEN_FIRST_ROW+LEN_FIRST_ROW-1)
	dblIdx = idx%(LEN_FIRST_ROW+LEN_FIRST_ROW-1)
	if dblIdx >= LEN_FIRST_ROW:
		return 2*(2*LEN_FIRST_ROW-dblIdx)-3 , dblRow*4+2
	return 2*dblIdx , dblRow*4



def parse_args(args,opts_without_values,opts_with_values):
	valopts = set(opts_with_values)
	aa = list()
	ao = dict()
	folarg = None
	optdone = False
	for i in args:
		if folarg is not None:
			ao[folarg] = i
			folarg=None
		elif optdone or (not i.startswith('-')):
			aa.append(i)
			optdone = True
		elif (i=="--") and (not optdone):
			optdone=True
		else:
			folarg=None
			for c in i[1:]:
				if folarg is not None:
					ao[folarg] = None
					folarg=None
				if c in valopts:
					folarg = c
				else:
					ao[c] = None

	for c in ao:
		if c in opts_without_values:
			pass
		elif c in opts_with_values:
			if ao[c] is None:
				sys.stderr.write("no value for opt -%s\n"%c)
				return (None,None)
		else:
			sys.stderr.write("unsupported option -%s\n"%c)
			return (None,None)

	return (aa,ao)



def color_calc_func_1(frameNo,seq_id,xx,yy):
	dot = (frameNo//7)%NUMLEDS
	t = 0.017*frameNo
	if (frameNo&128)==0:
		col_cyc_idx = xx
	else:
		col_cyc_idx = yy
	if dot==seq_id:
		return (1.0,1.0,1.0)
	return hsv2rgb_float(((t+0.125*col_cyc_idx)/3.0)%1.0,0.5,1.0)

def color_calc_func_2(frameNo,seq_id,xx,yy):
	xx = 0.5*(xx-13)
	yy = 0.4330127*(yy-6)		# sin(60deg)*0.5
	if xx==0.0 and yy==0.0:
		return (1.0,1.0,1.0)
	ang = math.atan2(yy,xx)
	h = ( ang*0.159154943 + 0.005*frameNo + 1.0 )%1.0
	return hsv2rgb_float( h , 0.6 , 0.8 )



if __name__=="__main__":
	sys.exit(main(sys.argv[1:]))
