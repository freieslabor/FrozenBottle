# Released by rdb under the Unlicense (unlicense.org)
# Based on information from:
# https://www.kernel.org/doc/Documentation/input/joystick-api.txt

from __future__ import print_function
import struct, array
from fcntl import ioctl
from threading import Thread
import sys
from queue import Queue, Empty
import time
import traceback

# These constants were borrowed from linux/input.h
AXIS_NAMES = {
	0x00 : 'x',
	0x01 : 'y',
	0x02 : 'z',
	0x03 : 'rx',
	0x04 : 'ry',
	0x05 : 'rz',
	0x06 : 'trottle',
	0x07 : 'rudder',
	0x08 : 'wheel',
	0x09 : 'gas',
	0x0a : 'brake',
	0x10 : 'hat0x',
	0x11 : 'hat0y',
	0x12 : 'hat1x',
	0x13 : 'hat1y',
	0x14 : 'hat2x',
	0x15 : 'hat2y',
	0x16 : 'hat3x',
	0x17 : 'hat3y',
	0x18 : 'pressure',
	0x19 : 'distance',
	0x1a : 'tilt_x',
	0x1b : 'tilt_y',
	0x1c : 'tool_width',
	0x20 : 'volume',
	0x28 : 'misc',
}

BUTTON_NAMES = {
	0x120 : 'trigger',
	0x121 : 'thumb',
	0x122 : 'thumb2',
	0x123 : 'top',
	0x124 : 'top2',
	0x125 : 'pinkie',
	0x126 : 'base',
	0x127 : 'base2',
	0x128 : 'base3',
	0x129 : 'base4',
	0x12a : 'base5',
	0x12b : 'base6',
	0x12f : 'dead',
	0x130 : 'a',
	0x131 : 'b',
	0x132 : 'c',
	0x133 : 'x',
	0x134 : 'y',
	0x135 : 'z',
	0x136 : 'tl',
	0x137 : 'tr',
	0x138 : 'tl2',
	0x139 : 'tr2',
	0x13a : 'select',
	0x13b : 'start',
	0x13c : 'mode',
	0x13d : 'thumbl',
	0x13e : 'thumbr',

	0x220 : 'dpad_up',
	0x221 : 'dpad_down',
	0x222 : 'dpad_left',
	0x223 : 'dpad_right',

	# XBox 360 controller uses these codes.
	0x2c0 : 'dpad_left',
	0x2c1 : 'dpad_right',
	0x2c2 : 'dpad_up',
	0x2c3 : 'dpad_down',
}

BUTTON2NONCANON = {
	"dpad_right": "\x1b[C",
	"dpad_left": "\x1b[D",
	"dpad_down": "\x1b[B",
	"a": "\x1b[A",
	"b": "\x1b[1",
	"start": "\n",
}


class GameController(Thread):
	def __init__(self, fn='/dev/input/js0'):
		Thread.__init__(self)

		# state store
		self.axis_states = {}
		self.button_states = {}

		self.queue = Queue()

		self.axis_map = []
		self.button_map = []

		# Open the joystick device.
		self.jsdev = open(fn, 'rb')

		# Get the device name.
		#buf = bytearray(63)
		buf = array.array('u', ['\0'] * 64)
		ioctl(self.jsdev, 0x80006a13 + (0x10000 * len(buf)), buf) # JSIOCGNAME(len)

		# Get number of axes and buttons.
		buf = array.array('B', [0])
		ioctl(self.jsdev, 0x80016a11, buf) # JSIOCGAXES
		num_axes = buf[0]

		buf = array.array('B', [0])
		ioctl(self.jsdev, 0x80016a12, buf) # JSIOCGBUTTONS
		num_buttons = buf[0]

		# Get the axis map.
		buf = array.array('B', [0] * 0x40)
		ioctl(self.jsdev, 0x80406a32, buf) # JSIOCGAXMAP

		for axis in buf[:num_axes]:
			axis_name = AXIS_NAMES.get(axis, 'unknown(0x%02x)' % axis)
			self.axis_map.append(axis_name)
			self.axis_states[axis_name] = 0.0

		# Get the button map.
		buf = array.array('H', [0] * 200)
		ioctl(self.jsdev, 0x80406a34, buf) # JSIOCGBTNMAP

		for btn in buf[:num_buttons]:
			btn_name = BUTTON_NAMES.get(btn, 'unknown(0x%03x)' % btn)
			self.button_map.append(btn_name)
			self.button_states[btn_name] = 0

		self.running = True

	def return_saved_button_state(self):
		for button, value in self.button_states.items():
			try:
				return BUTTON2NONCANON[button]
			except:
				pass

		return None

	def stop(self):
		self.running = False

	def run(self):
		try:
			while self.running:
				evbuf = self.jsdev.read(8)
				if evbuf:
					time_, value, type, number = struct.unpack('IhBB', evbuf)

					# buttons
					if type & 0x01:
						button = self.button_map[number]

						if value:
							self.queue.put(button)

					# axes
					"""
					if type & 0x02:
						axis = axis_map[number]
						if axis:
							fvalue = value / 32767.0
							axis_states[axis] = fvalue
							print "%s: %.3f" % (axis, fvalue)
					"""
		except Exception as e:
			with open("/tmp/frozen-bottle-gamepad.log", "a") as f:
				traceback.print_exc(file=f)
				self.running = False

	def getch(self):
		try:
			return BUTTON2NONCANON[self.queue.get(block=False)]
		except Empty:
			return None
		except Exception:
			return None

if __name__ == "__main__":
	import time
	ctrl = GameController()
	ctrl.start()
	while True:
		ch = ctrl.getch()
		if ch:
			print(repr(ch))
		time.sleep(0.2)
