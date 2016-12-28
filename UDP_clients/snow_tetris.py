#!/usr/bin/env python

# program to send some blinking to UDP for the flozen-bottle setup.


import time
import sys
import argparse
import LedClientBase
import random

DEFAULT_PORT = 8901
MATR_SIZE = 14

def shift_down(matr):

    rgb_matr = [[(0, 0, 0) for v in range(MATR_SIZE)]for i in range(MATR_SIZE)]

    for i in range(0, MATR_SIZE):
        for j in range(0, MATR_SIZE):
            rgb_matr[i][j] = matr[i][j]
           

    for i in range(0, MATR_SIZE-1):
        for j in range(0, MATR_SIZE):
            if(rgb_matr[i][j] == (0,0,0)):
                rgb_matr[i][j] = rgb_matr[i+1][j]
                rgb_matr[i+1][j] = (0,0,0)
                    
           
    #deletes full Line
    for i in range(MATR_SIZE-1):
        for j in range(MATR_SIZE):
            if(rgb_matr[i][j] != (1,1,1)):
                break
            if(j == MATR_SIZE-1):
                for x in range(MATR_SIZE):
                    rgb_matr[i][x] = (0,0,0)
                rgb_matr = shift_down(rgb_matr)

    for j in range(MATR_SIZE):
        if(rgb_matr[0][j] == (0,0,0)):
            break
        if(j == MATR_SIZE-1):
            for x in range(MATR_SIZE):
                rgb_matr[0][x] = (1,1,1)
    
    return rgb_matr


def get_smallest_line(matr):
    rgb_matr = [[(0, 0, 0) for v in range(MATR_SIZE)]for i in range(MATR_SIZE)]

    for i in range(0, MATR_SIZE):
        for j in range(0, MATR_SIZE):
            rgb_matr[i][j] = matr[i][j]
    
    for i in range(0, MATR_SIZE):
        for j in range(0, MATR_SIZE):
            if(rgb_matr[i][j] == (0,0,0)):
                return j
    return 0

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



        rgb_matr = [[(0, 0, 0) for v in range(MATR_SIZE)]for i in range(MATR_SIZE)]
	for i in xrange(0x7FFF0000):

                rgb_matr = shift_down(rgb_matr)

                rand = random.randrange(0, MATR_SIZE)
                while(rgb_matr[MATR_SIZE-1][rand] != (0,0,0)):
                    rand = random.randrange(0, MATR_SIZE)    
                
                r = random.uniform(0, 1.0)
                g = random.uniform(0, 1.0)
                b = random.uniform(0, 1.0)
                rgb_matr[MATR_SIZE-1][rand] = (r, g, b)


		lin = list()

                for i in range(MATR_SIZE):
                    for j in range(MATR_SIZE):
                        if(i%2 == 1):
                            if(j != MATR_SIZE-1):
                                lin.append(LedClientBase.rgbF_2_bytes(rgb_matr[i][(MATR_SIZE-2)-j]))
                        else:
                            lin.append(LedClientBase.rgbF_2_bytes(rgb_matr[i][j]))


                time.sleep(0.1)
		LedClientBase.send("".join(lin))

	LedClientBase.closedown()

	return 0



if __name__=="__main__":
	sys.exit(main(sys.argv[1:]))
