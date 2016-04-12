#!/usr/bin/env python

# server program to forward RGB data from UDP packets
# to serialport as XGRB 1555
# it supports a mapping to swap green and blue for some LEDs.


import socket
import sys
import time
import serial


UDPport = 8901

baudrate = 115200
serport = '/dev/ttyUSB0'

maxLED = 240

# mapping for the various types.
# 'a' means the color-mapping is GRB
# 'b' means the color-mapping is BRG
LEDmap = "aaababaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


sock = None
ser = None

def main(args):

	global sock
	global ser


	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	sock.bind(("0.0.0.0",UDPport))


	ser = serial.Serial(serport,baudrate,timeout=0,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,bytesize=8,rtscts=False,xonxoff=False)

	data = sock.recv(10000)

	print "start loop, listen-port %u" % UDPport
	try:
		while(data):
			print "UDP data %s" % repr(data)[:55]
			proc_input(data)
			data = sock.recv(10000)
	except socket.timeout:
		sock.close()


def proc_input(dat):
	global ser

	n = len(dat)//3
	if n>maxLED:
		n=maxLED
	ol = list()
	for i in xrange(n):
		# get 8-bit values
		c24 = dat[3*i:3*i+3]
		_r = ord(c24[0])
		_g = ord(c24[1])
		_b = ord(c24[2])
		# down-form to 5 bit
		_r = (_r>>3)&31
		_g = (_g>>3)&31
		_b = (_b>>3)&31
		# remap
		tp = LEDmap[i]
		if tp=='a':
			_c0=_g;_c1=_r;_c2=_b
		else:
			_c0=_b;_c1=_r;_c2=_g
		# reassemble to 16 bit 1:5:5:5
		val = (_c0<<10) + (_c1<<5) + (_c2)
		if i+1>=n:
			val += 0x8000
		ol.append(chr(val>>8)+chr(val&255))
	dat = (''.join(ol))+"SEQ-END."
	del ol

	ser.write(dat)


if __name__=='__main__':
	main(sys.argv[1:])


