#!/usr/bin/env python3

# program to send some blinking to UDP for the flozen-bottle setup.


import socket
import sys
import hex

DEFAULT_PORT = 8901

NUMLEDS = 189
LEN_FIRST_ROW = 14
NUM_ROWS = 14
ROW2_OVER_LEFT = False
ROW2_OVER_RIGHT = False

SEQ2POS = dict()	# filled in.
POS2SEQ = dict()





def connect(address,port=DEFAULT_PORT):
	global addr
	global sock
	if port is None:
		port = DEFAULT_PORT
	if address is None:
		#address = "127.0.0.1"
		address = "192.168.7.7"
	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	addr = (address,port)
	print("sending to UDP %s:%u" % (address,port))
	return True

def send(data):
	global addr
	global sock
	sock.sendto(data,addr)

def closedown():
	global sock
	sock.close()
	sock = None

def get_matching_HexBuff(defVal=0,border=0):
	# simply scan seq2pos and find minimum match. No efficient, but consistent if the format changes.
	res = hex.HexBuff(2,2) # dummy to get xy2wh function
	W,H = 0,0
	for xy in SEQ2POS.values():
		w,h = res.xy2wh(xy&0xFFFF,xy>>16)
		W = max(w,W)
		H = max(h,H)
	res = hex.HexBuff(W+1+2*border,H+1+2*border,border,border,None)
	# fill in all valid spaces with the defVal
	for xy in SEQ2POS.values():
		res.set_xy(xy&0xFFFF,xy>>16,defVal)
	return res

def hsv2rgb_float(h,s,v):
	""" convert a hsv value to a 3-tuple rgb. """
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
	""" convert a float-3-tuple to the pair of bytes, as chars. Returns a short string of 2 chars. """
	# pass in tuple
	r,g,b = rgb
	r = int(256.0*r)
	if r>255: r=255
	g = int(256.0*g)
	if g>255: g=255
	b = int(256.0*b)
	if b>255: b=255
	return bytes((r, g, b))

def seq_2_pos(idx):
	""" Convert the LED-sequence to an x/y coordinate pair. """
	dblRow = idx//(LEN_FIRST_ROW+LEN_FIRST_ROW-1)
	dblIdx = idx%(LEN_FIRST_ROW+LEN_FIRST_ROW-1)
	if dblIdx >= LEN_FIRST_ROW:
		return 2*(2*LEN_FIRST_ROW-dblIdx)-3 , dblRow*4+2
	return 2*dblIdx , dblRow*4


def seq_2_pos(idx):
	""" get position of a LED, in int coords. """
	global SEQ2POS
	if idx not in SEQ2POS:
		return None
	cod = SEQ2POS[idx]
	return (cod&0xFFFF) , (cod>>16)

def pos_2_seq(x,y):
	global POS2SEQ
	cod = x + (y<<16)
	if cod not in POS2SEQ:
		return None
	return POS2SEQ[cod]

def _fill_mappings(seq2pos, pos2seq):
	x=0;y=0
	if ROW2_OVER_LEFT: x=1
	maxX = x + 2*(LEN_FIRST_ROW-1)
	if ROW2_OVER_RIGHT: maxX+=1
	for sq in range(NUMLEDS):
		cod = x+(y<<16)
		seq2pos[sq] = cod
		pos2seq[cod] = sq
		#print("%3u   %2u|%2u" % (sq,x,y))
		if (y&2)==0:
			# to right
			x+=2
			if x>maxX:
				x+=1;y+=2
				while x>maxX:
					x-=2
		else:
			# to left
			x-=2
			if x<0:
				x-=1;y+=2
				while x<0:
					x+=2

_fill_mappings(SEQ2POS, POS2SEQ)
#for i in range(len(SEQ2POS)):
#	print("%3d 0x%08X" % (i,SEQ2POS[i]))

if __name__=="__main__":
	sys.exit(main(sys.argv[1:]))
