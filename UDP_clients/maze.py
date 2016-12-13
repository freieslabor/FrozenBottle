#!/usr/bin/env python

# random-maze in the frozen-bottle


import time
import math
import sys
import argparse
import LedClientBase
import hex

DEFAULT_PORT = 8901



def main(args):

	print "Das ist hinten und vorne nicht fertig..."
	return 5

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
	mz = get_matching_HexBuff(-1,0)

	dirs = hex.dir_wh

	tries=0
	idx=1
	while tries<1000:
		tries += 1
		w = random.randint(0,mz.w+1)
		h = random.randint(0,mz.h+1)
		v = mz.get_wh(w,h)
		if v != -1:
			continue
		nb = dict()
		nb[None]=None
		for dx,dy in dirs:
			vv = mz.get_wh(w+dx,h+dy)
			if vv>=0:
				if nc is not None:
					nc=None
					break
				nc=vv




	sys.exit(0)




	t = 0.0

	for i in xrange(0x7FFF0000):

		lin = list()
		for j in xrange(LedClientBase.NUMLEDS):
			(xx,yy) = LedClientBase.seq_2_pos(j)
			rgb_tuple = color_calc_func_1(i,j,xx,yy)


			lin.append(LedClientBase.rgbF_2_bytes(rgb_tuple))
		LedClientBase.send("".join(lin))

		time.sleep(0.040)
		t += 0.040

	LedClientBase.closedown()

	return 0


def grow(mz):
	dirs = hex.dir_wh
	tries=0
	idx=1
	while tries<1000:
		tries += 1
		w = random.randint(0,mz.w+1)
		h = random.randint(0,mz.h+1)
		v = mz.get_wh(w,h)
		if v != -1:
			continue
		nb = dict()
		for dx,dy in dirs:
			vv = mz.get_wh(w+dx,h+dy)
			if vv is None:
				continue
			cnt = 1
			if vv in nb:
				cnt = nb[vv]+1
			nb[vv] = cnt
		if len(nb)<=0:
			mz.set_wh(w,h,idx)
			idx += 1
		elif len(nb)==1:
			cnt = nb.values()[0]
			if cnt>1 and random.randint(0,255)<128:
				continue
			mz.set_wh(w,h,nb.keys()[0])
		else:
			grp = nb.values()[0]
			for dx,dy in dirs:
				vv = mz.get_wh(w+dx,h+dy)
				if vv is not None and vv>=0 and vv!=grp:
					#connect()
					pass




def connect(mz,w1,h1,w2,h2):
	pass


def color_calc_func_1(frameNo,seq_id,xx,yy):
	dot = (frameNo//7)%LedClientBase.NUMLEDS
	t = 0.017*frameNo
	if (frameNo&128)==0:
		col_cyc_idx = xx
	else:
		col_cyc_idx = yy
	if dot==seq_id:
		return (1.0,1.0,1.0)
	return LedClientBase.hsv2rgb_float(((t+0.125*col_cyc_idx)/3.0)%1.0,0.75,1.0)


if __name__=="__main__":
	sys.exit(main(sys.argv[1:]))
