#usr/bin/env python

import cv2

def main():
        while(True):
	        cap = cv2.VideoCapture(0)
                ret, im = cap.read()
                print ret
                if (ret):
                    cv2.imshow("Image",im)

if __name__=="__main__":
	main()
