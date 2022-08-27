#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Programm zum Eisntellen der Farbkorrektur für die verschiedenen Sorten an LEDs, 
# die im FrozenBottle verbaut sind und ein mittelgraues Bild 'wolkig' machen.
#
#
CTRLHELP = """
Steuerung:
  Tasten 1..6   Helligkeitsstufe. Es muss für alle Stufen die Farbe eingestellt werden.
  Taste z       Zone. Wahl welche der 4 Farbzonen eingestellt wird.
  Tasten u,i,o  R,G,B heller drehen.
  Tasten j,k,l  R,G,B dunkler drehen.
  Taste f       flash. aktuelle Farbzone durch blitzen hervorheben.
  Taste q       Beenden.
"""


import math
import sys
import time
import argparse
import LedClientBase
import noncanon_input

DEFAULT_PORT = 8901

NUM = LedClientBase.NUMLEDS
#NUM = 4

COMMAND_PCK_PREFIX = "COMMAND_2_SERVER"   # 16 byte command prefix string.

MEAN_GAMMA = 1.9

gammazone_names = ("l","w","g","b")



class adjpoint(object):
	__slots__=("bright","adj_r","adj_g","adj_b")

	def __init__(self,bright256):
		self.bright = int(bright256+0.5)
		if self.bright<0 or self.bright>255:
			raise ValueError("bright value of adjpoint must be in range 0..255")
		self.adj_r = 0
		self.adj_g = 0
		self.adj_b = 0

	def get_col(self):
		r = self.bright+self.adj_r
		g = self.bright+self.adj_g
		b = self.bright+self.adj_b
		r = min(max(r,0),255)
		g = min(max(g,0),255)
		b = min(max(b,0),255)
		return chr(r)+chr(g)+chr(b)

	def get_col0(self):
		r=g=b=self.bright
		return chr(r)+chr(g)+chr(b)

	def r_up(self):
		if self.adj_r >= 32: return
		self.adj_r += 2
		self.adj_g -= 1
		self.adj_b -= 1

	def g_up(self):
		if self.adj_g >= 32: return
		self.adj_r -= 1
		self.adj_g += 2
		self.adj_b -= 1

	def b_up(self):
		if self.adj_b >= 32: return
		self.adj_r -= 1
		self.adj_g -= 1
		self.adj_b += 2

	def r_down(self):
		if self.adj_r <= -32: return
		self.adj_r -= 2
		self.adj_g += 1
		self.adj_b += 1

	def g_down(self):
		if self.adj_g <= -32: return
		self.adj_r += 1
		self.adj_g -= 2
		self.adj_b += 1

	def b_down(self):
		if self.adj_b <= -32: return
		self.adj_r += 1
		self.adj_g += 1
		self.adj_b -= 2





#import math
#for i in xrange(1,7):
#	print 255.0*math.pow(i/7.0,1.9)

brightness_points = (24,51,88,135)  # ,190




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

	t = 0.0
	state = 1
	zone = 0

	# generate 'points'
	global points
	points = list()
	for tabname in gammazone_names:
		pl = list()
		for bright in brightness_points:
			pl.append(adjpoint(bright))
		points.append(pl)
	restore_points_settings()

	tio = noncanon_input.cio()
	num=100

	# send 'flat' gamma, basically disabling gamma curves in LED server.
	for zn in xrange(len(gammazone_names)):
		send_all_fake_gamma_curves(gammazone_names[zn],0.10)
	_do_quit = False


	flash = 0

	for i in xrange(0x7FFF0000):

		tmp = brightness_points[state]
		col = chr(tmp)+chr(tmp)+chr(tmp)
		data = col*num + "\0\0\0\0\0\0"*5;

		time.sleep(0.067)
		t += 0.067

		# process keyboard input
		while True:
			cc = tio.getch()
			if cc is None:
				break

			adj = False
			if len(cc)==1 and cc>="1" and cc<="9":
				tmp = ord(cc)-ord("1")
				if tmp<len(points[0]):
					state = tmp
			elif cc=="u":
				points[zone][state].r_up() ; adj = True
			elif cc=="i":
				points[zone][state].g_up() ; adj = True
			elif cc=="o":
				points[zone][state].b_up() ; adj = True
			elif cc=="j":
				points[zone][state].r_down() ; adj = True
			elif cc=="k":
				points[zone][state].g_down() ; adj = True
			elif cc=="l":
				points[zone][state].b_down() ; adj = True
			elif cc=="z":
				zone = (zone+1) % len(gammazone_names)
				flash=4
				print "now adjusting zone '%s'" % gammazone_names[zone]
			elif cc=="f":
				flash = 1
			elif cc=="+":
				num = min(num+1,189)
			elif cc=="-":
				num = max(num-1,0)
			elif cc=="g" or cc=="\x1B":
				gen_output_tables()
			elif cc=="q" or cc=="\x1B":
				_do_quit = True
			else:
				print "unknown input " + repr(cc)

			if adj:
				# was adjusted. build/send fake gamma curve to modify color.
				send_all_fake_gamma_curves(gammazone_names[zone],0.01)
				t += 0.03
				# Todo: ..... modify server/sim to accept three different gamma curves for each of the four zones.

		# flash?
		if flash>0:
			flash = (flash+1)%8
			if flash==0:
				send_all_fake_gamma_curves(gammazone_names[zone],0.01)
				t += 0.03
			else:
				gc = [(flash&1)*64+32]
				gc = gc*256
				send_gamma_curve(gammazone_names[zone],'g',gc)

		#send
		LedClientBase.send(data)
		#loop-delay
		time.sleep(0.08)
		t += 0.08

		if _do_quit:
			break


	LedClientBase.closedown()

	return 0

def send_flat_gamma1():
	for tbnam in gammazone_names:
		for chan in ("r","g","b"):
			send_gamma_curve(tbnam,chan,list(xrange(256)))
			time.sleep(0.05)

def send_gamma_curve(tabname,rgb,curvelist):
	""" given tab-name (one-char string), channel ("r","g" or "b") and curve (list-of-256-uint8) , send this to led-server """
	if len(curvelist)!=256:
		raise ValueError("curvelist must be list of 256 int values (in range 0..255)")
	if rgb not in ("r","g","b"):
		raise ValueError("channel must be one of r,g,b")
	cmd = list()
	cmd.append(COMMAND_PCK_PREFIX)
	cmd.append("GAMMA")
	cmd.append(tabname)
	cmd.append(rgb)
	cmd.append(",".join("%d"%b for b in curvelist))
	cmd = ' '.join(cmd)
	# print repr(cmd)
	LedClientBase.send(cmd)


def calc_gamma_curve(A,g):
	""" from A and g, calc the curve  y := A * x^g  . Returns array of ints (0..255) """
	res = list()
	for i in xrange(256):
		x = i/255.0
		y = int( A*math.pow(listX[i],g) + 0.5 )
		y = max(min(y,255),0)
		res.append(y)
	return res

def find_gamma_curve(listX,listY):
	""" try to find a function   y := A * x^g   , which most closely matches the values passed in. returns (A,g). """
	num = len(listX)
	if num != len(listY):
		raise ValueError("listX and listY should have same length")
	if max(listX)>1.0 or min(listX)<0.0:
		raise ValueError("listX must be values in the range 0 .. 1")
	if max(listY)>1.5 or min(listY)<0.0:
		raise ValueError("listX must be values in the range 0 .. 1.5")

	cur_g = 1.2
	cur_A = 1.0
	step_g = 0.2
	step_A = 0.2
	bestE = 1.0e30

	for loopcnt in xrange(40):
		tmp_bestE = 1.0e30;tmp_ig=0;tmp_iA=0
		for ig in xrange(-3,3+1,1):
			for iA in xrange(-3,3+1,1):
				# A,g for this run
				A = cur_A+iA*step_A
				g = cur_g+ig*step_g
				# calc sum-errors:
				E = 0.0
				for i in xrange(num):
					dif = listY[i] - A*math.pow(listX[i],g)
					E += dif*dif
				if E<tmp_bestE:
					tmp_bestE = E
					tmp_ig=ig
					tmp_iA=iA
		A = cur_A+tmp_iA*step_A
		g = cur_g+tmp_ig*step_g
		#print "run: tmp_ig=%d tmp_iA=%d, step_A=%.6f step_g=%.6f A=%.5f g=%.5f    sumE=%.8f" % (tmp_ig,tmp_iA,step_A,step_g,A,g,tmp_bestE)
		if tmp_iA*tmp_iA<9:
			step_A*=0.8
		if tmp_ig*tmp_ig<9:
			step_g*=0.8
		cur_A = A
		cur_g = g

	return (cur_A,cur_g)


def build_fake_gammacurves_from_points(tabname):
	# which tab?
	for zone in xrange(len(gammazone_names)):
		if gammazone_names[zone] == tabname:
			break
	else:
		raise ValueError("invalid tabname. must be in list gammazone_names")
	# get/build points list.
	pts = list()
	for pt in points[zone]:
		x = pt.bright
		yr = pt.bright + pt.adj_r
		yg = pt.bright + pt.adj_g
		yb = pt.bright + pt.adj_b
		pts.append((x,yr,yg,yb))
	pts.sort()
	if pts[0][0]>0:
		pts.insert(0,(0,0,0,0))
	if pts[-1][0]<255:
		pts.insert(len(pts),(255,255,255,255))

	# do linear piece-by-piece interpolation
	here = 0
	last = (0,0,0,0)
	res = list()
	for x in xrange(256):
		if x>pts[here][0]:
			last = pts[here]
			here+=1
		if x==pts[here][0]:
			r,g,b = pts[here][1:]
		else:
			fac = (x-last[0])/float(pts[here][0]-last[0])
			r = int( last[1] + fac*float(pts[here][1]-last[1]) + 0.5 )
			g = int( last[1] + fac*float(pts[here][1]-last[1]) + 0.5 )
			b = int( last[1] + fac*float(pts[here][1]-last[1]) + 0.5 )
		r = min(max(r,0),255)
		g = min(max(g,0),255)
		b = min(max(b,0),255)
		res.append((x,r,g,b))
	res_r = list()
	res_g = list()
	res_b = list()
	for x in xrange(256):
#		print repr(res[x])
		res_r.append(res[x][1])
		res_g.append(res[x][2])
		res_b.append(res[x][3])
	return res_r,res_g,res_b

def send_all_fake_gamma_curves(tabname,t_delay = None):
	if t_delay is None or t_delay<=0.0:
		t_delay=0.0
	fake_gamma_r,fake_gamma_g,fake_gamma_b = build_fake_gammacurves_from_points(tabname)
	# send to server for current colorgroup
	send_gamma_curve(tabname,"r",fake_gamma_r) ; time.sleep(t_delay)
	send_gamma_curve(tabname,"g",fake_gamma_g) ; time.sleep(t_delay)
	send_gamma_curve(tabname,"b",fake_gamma_b) ; time.sleep(t_delay)

def gen_output_tables():
	# first, table to keep adjustments in this program.
	res = list()
	a = res.append
	a("def restore_points_settings():")
	for zone in xrange(len(gammazone_names)):
		for bl in xrange(len(points[zone])):
			p = points[zone][bl]
			if p.adj_r != 0: a("  points[%d][%d].adj_r = %d"%(zone,bl,p.adj_r))
			if p.adj_g != 0: a("  points[%d][%d].adj_g = %d"%(zone,bl,p.adj_g))
			if p.adj_b != 0: a("  points[%d][%d].adj_b = %d"%(zone,bl,p.adj_b))
	if len(res)==1:
		a("  pass")
	print "\n"
	print "\n".join(res)
	print "\n"

	# second, generate gamma tables for server
	res = list()
	a = res.append
	# ...... TODO: add this.
	# calc 'x' values for the bright values
	xv = list()
	for bright in brightness_points:
		xv.append( int(255.0*math.pow(bright/255.0,1.0/MEAN_GAMMA)+0.5) )
	a("static const float gamma_curve_cal_values[NUM_GAMMA_CURVES][3][2] =")
	a("{")
	for zone in xrange(len(gammazone_names)):
		tabnam = gammazone_names[zone]
		pp = list()
		for chan in ('r','g','b'):
			adjnam = 'adj_'+chan
			listX=list()
			listY=list()
			for bl in xrange(len(brightness_points)):
				bright = brightness_points[bl]
				_adj = getattr( points[zone][bl] , adjnam )
				listX.append(xv[bl]/255.0)
				listY.append((bright+_adj)/255.0)
			# now estimate gamma curve
			_A,_g = find_gamma_curve(listX,listY)
#			print "gamma curve for zone '%s' for '%s':  A=%.3f  g=%.3f" % (tabnam,chan,_A,_g)
			pp.append("{%.3f,%.3f}"%(_A,_g))
		a("  {%s},// Zone '%s'"%(",".join(pp),tabnam))
	a("}")

	print "\n"
	print "\n".join(res)
	print "\n"


def restore_points_settings():
  points[0][0].adj_r = 2
  points[0][0].adj_g = 2
  points[0][0].adj_b = -4
  points[0][1].adj_r = 9
  points[0][1].adj_g = 6
  points[0][1].adj_b = -15
  points[0][2].adj_r = 15
  points[0][2].adj_g = 12
  points[0][2].adj_b = -27
  points[0][3].adj_r = 15
  points[0][3].adj_g = 18
  points[0][3].adj_b = -33
  points[2][0].adj_r = -4
  points[2][0].adj_g = -1
  points[2][0].adj_b = 5
  points[2][1].adj_r = -7
  points[2][1].adj_g = -1
  points[2][1].adj_b = 8
  points[2][2].adj_r = -11
  points[2][2].adj_g = -2
  points[2][2].adj_b = 13
  points[2][3].adj_r = -5
  points[2][3].adj_g = -5
  points[2][3].adj_b = 10
  points[3][0].adj_r = 3
  points[3][0].adj_b = -3
  points[3][1].adj_r = 18
  points[3][1].adj_g = -3
  points[3][1].adj_b = -15
  points[3][2].adj_r = 28
  points[3][2].adj_g = -5
  points[3][2].adj_b = -23
  points[3][3].adj_r = 40
  points[3][3].adj_g = -8
  points[3][3].adj_b = -32


if __name__=="__main__":
	if False:
		# ugly test or debug code.
		(A,g) = find_gamma_curve( (0.0,0.25,0.5,0.75,1.0) , (0.0,0.1,0.4,0.7,1.1) )
		print repr((A,g))
		sys.exit(1)
	sys.exit(main(sys.argv[1:]))
