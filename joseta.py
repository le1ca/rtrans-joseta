#!/usr/bin/env python

# This is a simulator implementing the protocol for Jose's sensor board.
# It will be useful in testing the Launchpad's communication.

import serial, struct, time
from threading import Timer
import random

START_BYTE = 0xFF
ESCAPE_BYTE = 0xFE
streaming = True
timer = None
second_delay = 1

def persistent_timer(delay, callback, args=None, kwargs=None):

    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}

    def run_event(*args2, **kwargs2):
        if streaming:
            callback(*args2, **kwargs2)
            new_timer = Timer(delay, run_event, args2, kwargs2)
            new_timer.start()

    return Timer(delay, run_event, args, kwargs)


def escape(b):
    """
    Returns a list of bytes - either a list consisting of only the input (i.e. [b])
    or a list consisting of an escape byte and the input (i.e. [\, b]).
    """
    # Only special bytes need escaping. For now, those are only the start byte and the escape byte itself.
    if b in (START_BYTE, ESCAPE_BYTE):
        return [ESCAPE_BYTE, b]
    else:
        return [b]

class josetasim:

    # initialize the uart tty
    def __init__(self, tty, baud):
        self._tty = serial.Serial(tty, baud, timeout=None)
        self._time = None

    # send an array of bytes on the uart
    def _send(self, l):
        # print("Outgoing message of %d bytes" % len(l))

        ### simulated packet loss
        if random.random() > 0.9:
            print("Outgoing packet is corrupted")
            l = l[:5] + l[6:]

        ### calculate CRC
        crc_raw = self._outgoing_crc(l)
        crc_part1, crc_part2 = [ord(x) for x in struct.pack('H',crc_raw)]
        l.append(crc_part1)
        l.append(crc_part2)

        ### escape
        byte_lists = [escape(b) for b in l]
        l = [b for sublist in byte_lists for b in sublist]  # flatten
        
        ### start byte
        l.insert(0, START_BYTE)

        for b in l:
            bb = bytes(chr(b))
            self._tty.write(bb)
            #time.sleep(0.01)

    # read a 3-byte command sequence
    def _read(self):
        return [ord(self._tty.read(1)[0]) for i in range(0, 3)]
        
    def _outgoing_crc(self, data):
        crc = 0
        for x in data:
                x = ((crc >> 8) ^ x) & 0xFF
                x = (x ^ x >> 4) & 0xFF
                crc = ((crc << 8)&0xFFFF) ^ ((x << 12)&0xFFFF) ^ ((x << 5)&0xFFFF) ^ (x&0xFFFF)
        
        return crc

    # build a data packet
    def _build_data(self, ts):
        c = []
        print("Building packet with ts %d" % ts)

        c.append(0x00) # FLAGS
        c.append(0xe0) # VOLTAGE
        c.append(0x2e)
        c.append(0x64) # CURRENT
        c.append(0x00)
        c.append(0x10) # PHASE
        c.append(0x00)
        c.append(0x14) # TEMPERATURE
        c.append((ts & 0x000000FF) >> 0 ) # TIMESTAMP
        c.append((ts & 0x0000FF00) >> 8 )
        c.append((ts & 0x00FF0000) >> 16)
        c.append((ts & 0xFF000000) >> 24)
        c.append(0x00) # RESERVED
        c.append(0x00) # ERROR

        return c
        
    # build the initialization packet
    def _build_init(self):
        c = []

        c.append(0x00) # FLAGS
        c.append(0x00) # VOLTAGE
        c.append(0x00)
        c.append(0x00) # CURRENT
        c.append(0x00)
        c.append(0x00) # PHASE
        c.append(0x00)
        c.append(0x00) # TEMPERATURE
        c.append(0x00) # TIMESTAMP
        c.append(0x00)
        c.append(0x00)
        c.append(0x00)
        c.append(0x00) # RESERVED
        c.append(0x80) # ERROR

        return c

    def _checksum(self, byte1, byte2):
        return 0xFF - ((byte1 + byte2) & 0xFF)
        
    # process a command
    def _process(self, c):
    
        print("Incoming command: %s" % c)
        
        # data req
        # if c[0] & 0xF0 == 0x10:
        #     if self._time is not None:
        #         curtime = int(time.time()) - self._time
        #         print("Current time is %d" % curtime)
        #     else:
        #         print("Current time is not set")
        #     if c[1] & 0xF0 == 0xF0:
        #         for d in reversed(xrange(0,60)):
        #             self._send(self._build_data(curtime - d))
        #     else:
        #         offset = (c[1] & 0x70) >> 4
        #         for d in xrange(0, 4):
        #             self._send(self._build_data(curtime - 60 + offset + d))



        # ctrl set
        if c[0] & 0xF0 == 0x20:
            msg = "Control set: "
            if c[1] & 0x80:
                msg += "[O] occupancy sensor trigger "
            if c[1] & 0x40:
                msg += "[T] temperature range trigger "
            if c[1] & 0x20:
                msg += "[X] manual relay control "
            if c[1] & 0x10:
                msg += "[E] default relay state "
            if c[1] & 0xF0 == 0x00:
                msg += "Unknown control"

            print(msg)
            
        # temp set
        elif c[0] & 0xF0 == 0x30:
            msg = "Temperature set: "

            if c[1] & 0xF0:
                msg += "(high) "
            else:
                msg += "(low) "

            msg += str(c[1] & 0x7f)
            
        # time set or reset
        elif c[0] & 0xF0 == 0x40:

            # reset unit
            if c[1] & 0x80 == 0x00:
                print("Reset unit")
                time.sleep(1)
                self._send(self._build_init())
                
            # set time
            else:
                print("Epoch timestamp is %d" % (c[1] & 0x7F))
                self._time = int(time.time()) - (c[1] & 0x7F)

        # stream rate and on/off
        elif c[0] & 0xF0 == 0x50:
            global streaming
            global second_delay
            global timer
            if c[1] & 0x80 == 0x80:
                streaming = True
            else:
                streaming = False

            if c[1] & 0x7F == 0:
                # keep rate as-is
                pass
            else:
                second_delay = c[1] & 0x7F
                # referencing the old timer.function ensures that this timer still repeats
                timer = Timer(second_delay, timer.function, timer.args, timer.kwargs)


    # start command loop
    def start(self):
        def send_frames(seconds_elapsed):
            if self._time is not None:
                curtime = int(time.time()) - self._time
            else:
                curtime = 0
            packets = [self._build_data(curtime - n) for n in reversed(range(1, seconds_elapsed+1))]
            for packet in packets:
                self._send(packet)
        timer = persistent_timer(second_delay, send_frames, (second_delay,))
        timer.start()
        while True:
            self._process(self._read())
        


if __name__ == "__main__":
    j = josetasim('/dev/ttyUSB0', 9600)
    j.start()

