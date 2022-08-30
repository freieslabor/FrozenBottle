#!/usr/bin/env python3

# server program to forward RGB data from UDP packets
# to serialport as XGRB 1555
# it supports a mapping to swap green and blue for some LEDs.


import argparse
import math
import socket
import sys
import time
import rpi_ws281x as neopixel


UDPport = 8901

baudrate = 115200


# LED strip configuration:
LED_COUNT      = 189      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
POWERLIMIT     = 100     # If average is above this, scale down all brightess values.


maxLED = LED_COUNT  # for I/O packets



sock = None
strip = None
arr = None
count = 0

def main(args):

	global sock
	global strip


	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	sock.bind(("0.0.0.0",UDPport))

	# initialize the strip.
	print("... create ...")
	strip = neopixel.Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, strip_type=neopixel.WS2811_STRIP_RGB)
	# Intialize the library (must be called once before other functions).
	print("... done ... start ...")
	strip.begin()
	print("... done ...")

	load_default_gammacurves()

	print("start loop, listen-port {UDPport}")

	data = sock.recv(10000)


	try:
		while(data):
			## #print(f"UDP data {repr(data)[:55]}")
			proc_input(data)
			data = sock.recv(10000)
	except socket.timeout:
		sock.close()

	print("exiting...")
	time.sleep(0.25)

	return 0


# Eine Zeile Input verarbeiten: Auf 5-bit kuerzen, RGB Komponenten umordnen, alles an tty senden.
def proc_input(dat):
	global strip
	global arr
	global count

	count += 1

	n = len(dat)//3
	if n>maxLED:
		n=maxLED
	ol = list()
	if arr is None:
		arr=list()
	while len(arr) < 3*n:
		arr.append(0)

	for i in range(0,3*n,3):
		# get 8-bit values
		c24 = dat[i:i+3]
		arr[i+0] = c24[0]
		arr[i+1] = c24[1]
		arr[i+2] = c24[2]

	# filter .....
	arr = fix_and_filter(arr)

	# send to neopixel
	for i in range(0,3*n,3):
		strip.setPixelColor(i//3,neopixel.Color( * arr[i:i+3] ))

	strip.show()

#	if not (count%10):
#		print(f"dat = {repr(dat)}")
#		print(f"arr = {repr(arr)}")

#	if not (count%100):
#		print(f"count = {count}")


# mapping for the various types.
# 'a' means the color-mapping is GRB
# 'b' means the color-mapping is BRG
# Einstellen: alle auf 'a', ganz-gruenes Bild senden, dann fuer alle blauen LEDs Buchstaben auf 'b' aendern.
fix_map_GBswap = "".join([
	"aaaaaababbaaaa" ,
	"aabaababaaaaa"  ,
	"aabaaaabbaaaaa" ,
	"aaaaaabaabbaa"  ,
	"bbbbabbabaaaaa" ,
	"ababaaaababaa"  ,
	"babbbabaabbbaa" ,
	"abbaaabbbbbab"  ,
	"baabaabaababaa" ,
	"aabaabaababaa"  ,
	"aabaaaaaaaaaaa" ,
	"abbbbaabaabbb"  ,
	"aabbbaaababbba" ,
	"ababaaabbbaaa"  ,
	"aaaaaaaaaaaaaa" ,
	"aaaaaaaaaaaaa"
])

if len(fix_map_GBswap)<1024:
	fix_map_GBswap = fix_map_GBswap + ('a'*(1024-len(fix_map_GBswap)))


NUM_GAMMA_CURVES = 4

fix_map_4types = "".join([
	"gwgwwwbwlbwglw" ,
	"lwblglgllgggw"  ,
	"glllgglbbgwgwg" ,
	"wwwllgblglblw"  ,
	"blllwlbgllwlww" ,
	"llllwlglbwbll"  ,
	"bllllgblwllbll" ,
	"llllglblbllll"  ,
	"lwglwllwgbwlll" ,
	"lwlgwlwgbwlll"  ,
	"lwlgwgwwggwglw" ,
	"llllllwllglbl"  ,
	"wllbbggglllllg" ,
	"gbbbgglbbllgg"
])


gamma_curve_cal_values = (
  ((1.102,1.836),(1.156,1.942),(0.771,1.998)), # Zone 'l'
  ((1.008,1.913),(1.008,1.913),(1.008,1.913)), # Zone 'w'
  ((1.044,2.155),(0.965,1.888),(1.034,1.754)), # Zone 'g'
  ((1.316,1.915),(0.938,1.885),(0.771,1.946)), # Zone 'b'
)

chr_2_gammano = {'w':1,'g':2,'b':3,'l':0}


gamma4 = list()
for i in range(4):
	sb = list()
	for j in range(4):
		sb.append([0][:]*256)
	gamma4.append(sb)


def load_default_gammacurves():

	global gamma4

	for zn in range(NUM_GAMMA_CURVES):
		for rgb in range(3):
			A = gamma_curve_cal_values[zn][rgb][0]
			g = gamma_curve_cal_values[zn][rgb][1]

			for i in range(256):
				val = int( 255.0*A*math.pow(i/255.0,g) + 0.5 )
				if val>255:
					val=255
				gamma4[zn][rgb][i] = val



def fix_and_filter(ar):

	numleds = len(ar)//3
	summax = POWERLIMIT*numleds
	sumpwr = 0

	for i in range(numleds):
		i3 = i*3
		r=ar[i3+0];
		g=ar[i3+1];
		b=ar[i3+2];
		if i<len(fix_map_4types):
			sym = chr_2_gammano[fix_map_4types[i]]
		else:
			sym = 1

		r = gamma4[sym][0][r]
		g = gamma4[sym][1][g]
		b = gamma4[sym][2][b]

		# check mapping table to swap blue- and green-parts.
		if i>=len(fix_map_GBswap) or fix_map_GBswap[i]!='b' :
			# type 'a' is G-R-B
			ar[i3+0]=g;
			ar[i3+1]=r;
			ar[i3+2]=b;
		else:
			# type 'b' is B-R-G
			ar[i3+0]=b;
			ar[i3+1]=r;
			ar[i3+2]=g;

		# sum power
		sumpwr += (r+g+b)

	if sumpwr > summax:
		quot = float(summax)/float(sumpwr)
		for i in range(len(ar)):
			ar[i] = int(ar[i]*quot+0.5)

	return ar





if __name__=='__main__':
	sys.exit(main(sys.argv[1:]))


