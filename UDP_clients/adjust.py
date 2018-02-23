#!/usr/bin/env python

# program to send some blinking to UDP for the flozen-bottle setup.


import time
import sys
import argparse
import LedClientBase
import noncanon_input

DEFAULT_PORT = 8901

NUM = LedClientBase.NUMLEDS
#NUM = 4

# static patterns. all gray.
GRAY = (
	"\x00\x00\x00"*NUM,
	"\x33\x33\x33"*NUM,
	"\x66\x66\x66"*NUM,
	"\x99\x99\x99"*NUM,
	"\xCC\xCC\xCC"*NUM,
	"\xFF\xFF\xFF"*NUM
)

state = 1;

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

	tio = noncanon_input.cio()
	num=4

	for i in xrange(0x7FFF0000):

		data = GRAY[state][:3]*num + "\0\0\0\0\0\0"*5;

		time.sleep(0.067)
		t += 0.067

		# process keyboard input
		while True:
			cc = tio.getch()
			if cc is None:
				break
			print(repr(cc))

			if cc=="1":
				state = 0
			elif cc=="2":
				state = 1
			elif cc=="3":
				state = 2
			elif cc=="4":
				state = 3
			elif cc=="5":
				state = 4
			elif cc=="6":
				state = 5
			elif cc=="+":
				num = min(num+1,189)
			elif cc=="-":
				num = max(num-1,0)

		#send
		LedClientBase.send(data)
		#loop-delay
		time.sleep(0.08)
		t += 0.08



	LedClientBase.closedown()

	return 0



if __name__=="__main__":
	sys.exit(main(sys.argv[1:]))
