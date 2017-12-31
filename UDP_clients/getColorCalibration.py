#usr/bin/env python

import pyscreenshot as ImageGrab
import argparse
import cv2
import numpy as np
from PIL import Image
import math
import os.path
import sys
import time
import LedClientBase
import hex

DEFAULT_PORT = 8901

def main(args):
	parser = argparse.ArgumentParser()
	parser.add_argument("address",type=str,help="UDP address")
	parser.add_argument("-p","--port",type=int,help="UDP port number")
	args = parser.parse_args()

#	print repr(aa)

	cap = cv2.VideoCapture(0)

        port = DEFAULT_PORT
	address = "127.0.0.1"
        

        if args.port is not None:
		port = args.port

	if port<=0 or port==0xFFFF:
		sys.stderr.write("bad port number %u\n"%port)
		return 1

	if args.address is not None:
		address = args.address

	LedClientBase.connect(address,port)

	mainbuff = hex.HexBuff(21,16,0,0,(0.0,0.0,0.0))
	l = list()

        for i in range(1+LedClientBase.NUMLEDS):
		# now prepare and send
                if(i == 0):
	            mainbuff.fill_val((0,0,0.2))
                if(i>0):
	            mainbuff.fill_val((0,0,0))
		    (xx,yy) = LedClientBase.seq_2_pos(i-1)
                    mainbuff.set_xy(xx,yy,(0,0,0.1))
                    print(i)
		lin = list()
		for j in xrange(LedClientBase.NUMLEDS):
			(xx,yy) = LedClientBase.seq_2_pos(j)
			rgb_tuple = mainbuff.get_xy(xx,yy)

			lin.append(LedClientBase.rgbF_2_bytes(rgb_tuple))
		LedClientBase.send("".join(lin))
                if(i == 0):
                    #im=ImageGrab.grab(bbox=(640,20,1280,800)) # X1,Y1,X2,Y2
                    #im.save('a.png')
                    #im = cv2.imread('a.png')
                    ret, im =cap.read()
                    lower=[200,0,0]
                    lower=np.array(lower,dtype="uint8")
                    upper=[255,250,250]
                    upper = np.array(upper,dtype="uint8")
                    allmask = cv2.inRange(im,lower,upper)
                else:
                    time.sleep(1)
                    im = cv2.bitwise_and(im,im,mask=allmask)
                    #cv2.imwrite('b.png',im)
                    cv2.imshow("Image",im)
                    cv2.waitKey()
	LedClientBase.closedown()
	return 0

if __name__=="__main__":
	sys.exit(main(sys.argv[1:]))
