import sys
#-- include('examples/showgrabbox.py')--#
import pyscreenshot as ImageGrab

def main(args):
    im=ImageGrab.grab(bbox=(10,10,510,510)) # X1,Y1,X2,Y2
    im.show()

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
