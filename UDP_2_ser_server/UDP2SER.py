#!/usr/bin/env python

# server program to forward RGB data from UDP packets
# to serialport as XGRB 1555
# it supports a mapping to swap green and blue for some LEDs.


import socket
import sys
import serial
from datetime import datetime, timedelta


UDPport = 8901

baudrate = 115200
serport = '/dev/ttyUSB0'

maxLED = 240

# mapping for the various types.
# 'a' means the color-mapping is GRB
# 'b' means the color-mapping is BRG
# Einstellen: alle auf 'a', ganz-gruenes Bild senden, dann fuer alle blauen
# LEDs Buchstaben auf 'b' aendern.
LEDmap = (
           "ababaababaabbb" +
           "bbbbbbbbabbbb" +
           "bbbaaabbbbbbaa" +
           "aabbbbbbabaab" +
           "bbaabbbbabbbaa" +
           "abbbbaaabbbbb" +
           "baabaaaaabbaaa" +
           "bbabbaabbbbba" +
           "ababbaaaaaaaaa" +
           "aaaaaaaaaaaaa" +
           "aaaaaaaaaaaaaa" +
           "aaaaaaaaaaaaa" +
           "aaaaaaaaaaaaaa" +
           "aaaaaaaaaaaaa" +
           "aaaaaaaaaaaaaa" +
           "aaaaaaaaaaaaa")

# slot length in seconds
SLOT_LENGTH = 30

# send data timeout in seconds
DATA_TIMEOUT = 2

# list of (address, timeslot_end_time, timeout_time) tuples
CLIENTS = []

# list of IPs that are always allowed sending
IP_WHITELIST = ["127.0.0.2"]


if len(LEDmap) < 1024:
    LEDmap = LEDmap + ('a' * (1024 - len(LEDmap)))


sock = None
ser = None


def main(args):

    global sock
    global ser

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", UDPport))

    ser = serial.Serial(serport, baudrate, timeout=0,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE, bytesize=8, rtscts=False,
                        xonxoff=False)

    data, address = sock.recvfrom(10000)

    print("start loop, listen-port {}".format(UDPport))
    print("sending to {}".format(serport))
    try:
        while(data):
            # print("UDP data {}".format(repr(data)[:55]))
            multi_client(data, address[0])

            data, address = sock.recvfrom(10000)
    except socket.timeout:
        sock.close()

    return 0


def multi_client(data, address):
    """
    As receiving data from multiple clients at the same time does not make
    sense this method makes sure only one client can send data. Client
    management is done with timeslots. Each client requests a timeslot by
    sending data. If the timeslot has ended the next client is granted a slot.
    """

    global CLIENTS, IP_WHITELIST, SLOT_LENGTH, DATA_TIMEOUT

    if len(CLIENTS) > 0:
        # cleanup expired timeslot and client not sending data
        client_addr, end_time, last_data_time = CLIENTS[0]
        end_time_exceeded = end_time and datetime.now() > end_time
        timeout = last_data_time and \
            datetime.now() > last_data_time + timedelta(seconds=DATA_TIMEOUT)

        if end_time_exceeded or timeout:
            print("Cleaning {} (exceeded: {}; timeout: {})"
                  .format(client_addr, end_time_exceeded, timeout))
            del CLIENTS[0]

    # check if client is new
    found = False

    for client in CLIENTS:
        client_addr, end_time, last_data_time = client
        if client_addr == address:
            found = True

    if not found:
        # whitelisted clients get priority
        if address in IP_WHITELIST:
            priority_length = datetime.now() + timedelta(hours=24)
            CLIENTS.insert(0, (address, priority_length, None))
            print("New priority client {} connected".format(address))
        else:
            CLIENTS.append((address, None, None))
            print("New client {} connected".format(address))

    # client address is at 1st position in queue
    client_addr, end_time, last_data_time = CLIENTS[0]
    if client_addr == address:
        # first data received from client
        if end_time is None:
            end_time = datetime.now() + timedelta(seconds=SLOT_LENGTH)
        CLIENTS[0] = (client_addr, end_time, datetime.now())

        print("{} is sending data".format(address))
        proc_input(data)
    else:
        client = list(filter(lambda c: c[0] == address, CLIENTS))[0]
        position = CLIENTS.index(client)
        print("{} tried to send data, but is queued (position {})"
              .format(address, position))


# Eine Zeile Input verarbeiten: Auf 5-bit kuerzen, RGB Komponenten umordnen,
# alles an tty senden.
def proc_input(dat):
    global ser

    n = len(dat)//3
    if n > maxLED:
        n = maxLED
    ol = list()
    for i in xrange(n):
        # get 8-bit values
        c24 = dat[3*i:3*i+3]
        _r = ord(c24[0])
        _g = ord(c24[1])
        _b = ord(c24[2])

        # down-form to 5 bit
        _r = (_r >> 3) & 31
        _g = (_g >> 3) & 31
        _b = (_b >> 3) & 31

        # remap
        tp = LEDmap[i]
        if tp == 'a':
            _c0 = _g
            _c1 = _r
            _c2 = _b
        else:
            _c0 = _b
            _c1 = _r
            _c2 = _g

        # reassemble to 16 bit 1:5:5:5
        val = (_c0 << 10) + (_c1 << 5) + (_c2)
        if i+1 >= n:
            val += 0x8000
        ol.append(chr(val >> 8) + chr(val & 255))
    dat = (''.join(ol)) + "SEQ-END."
    del ol

    # print(repr(dat)[:70])
    ser.write(dat)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
