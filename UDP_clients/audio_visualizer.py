#!/usr/bin/env python

# based on https://github.com/karlstav/cava/issues/123#issuecomment-307891020
# by worron <worrongm@gmail.com>

# audio visualizier for Frozen Bottle.

import sys
import argparse
import os
import struct
import subprocess
import tempfile

import LedClientBase

DEFAULT_PORT = 8901
BARS_NUMBER = 14
RAW_TARGET = "/dev/stdout"

conpat = """
[general]
bars = %d
[output]
channels = mono
method = raw
raw_target = %s
bit_format = 8bit
"""

config = conpat % (BARS_NUMBER, RAW_TARGET)
bytetype, bytesize, bytenorm = ("B", 1, 255)  # 8bit


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

	if port <= 0 or port == 0xFFFF:
		sys.stderr.write("bad port number %u\n"%port)
		return 1

	if aa.address is not None:
		address = aa.address

	if not LedClientBase.connect(address,port):
		return 1

	with tempfile.NamedTemporaryFile() as config_file:
		config_file.write(config.encode())
		config_file.flush()

		cava = subprocess.Popen(["cava", "-p", config_file.name], stdout=subprocess.PIPE)
		chunk = bytesize * BARS_NUMBER
		fmt = bytetype * BARS_NUMBER

		try:
			while True:
				data = cava.stdout.read(chunk)
				if len(data) < chunk:
					break
				samples = [i for i in struct.unpack(fmt, data)]  # raw values without norming

				lin = list()
				for j in xrange(LedClientBase.NUMLEDS):
					(xx,yy) = LedClientBase.seq_2_pos(j)
					h = samples[xx//2]
					if h > 6 * yy:
						# farbe
						rgb_tuple = (1, 0, 0)
					else:
						# schwarz
						rgb_tuple = (0, 0, 0)

					lin.append(LedClientBase.rgbF_2_bytes(rgb_tuple))
				LedClientBase.send("".join(lin))

		finally:
			LedClientBase.closedown()

		return 0


if __name__=="__main__":
	sys.exit(main(sys.argv[1:]))
