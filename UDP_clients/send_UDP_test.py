#!/usr/bin/env python

# program to send some blinking to UDP for the flozen-bottle setup.

ADDRESS = "192.168.7.7"
#ADDRESS = "127.0.0.1"
PORT = 8901

import socket
import sys
import time

NUM_LEDS=64

def main(args):

	(aa,ao) = parse_args( args , () , ('p') )

	if aa is None:
		return 1

	print repr(aa)
	print repr(ao)

	if len(aa) > 0:
		sys.stderr.write("cannot use args %s\n"%repr(aa))
		return 1

	port = PORT

	if 'p' in ao:
		port = int(ao['p'])
		if port<=0 or port==0xFFFF:
			sys.stderr.write("bad port number %u\n"%port)
			return 1



	s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	host = ADDRESS
	buf = 1024
	addr = (host,port)


	cols  = ("\xC0\x30\x30","\x30\xC0\x30","\x30\x30\xC0","\xB0\xB0\xB0")
	cols0 = ("\x80\x00\x00","\x00\x80\x00","\x00\x00\x80","\x70\x70\x70")

	print "sending to %s:%u" % (host,port)

	for i in xrange(40000):
		print " i = %u" % i
		c = cols[(i//17)%4]
		c0 = cols0[(i//17)%4]
		leng = NUM_LEDS
		pos = i%leng
		line = (c0*pos) + c + (c0*(leng-1-pos))
		s.sendto(line,addr)
		time.sleep(0.1)


	s.close()



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



if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))



