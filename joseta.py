#!/usr/bin/env python

# This is a simulator implementing the protocol for Jose's sensor board.
# It will be useful in testing the Launchpad's communication.

import serial, struct, time
from PyCRC.CRC16 import CRC16

class josetasim:

    # initialize the uart tty
    def __init__(self, tty, baud):
        self._tty = serial.Serial(tty, baud, timeout=None)
        self._time = None

    # send an array of bytes on the uart
    def _send(self, l):
        #print("Outgoing message of %d bytes" % len(l))
        for b in l:
            bb = bytes(chr(b))
            self._tty.write(bb)
            time.sleep(0.01)

    # read a 3-byte command sequence
    def _read(self):
        return [ord(self._tty.read(1)[0]) for i in range(0, 3)]
        
    def _outgoing_crc(self, data):
        #crc = 0
        #x = 0
        #for part in parts:
        #    x = crc >> 8 ^ part
        #    x = x ^ (x >> 4)
        #    crc = (crc << 8) ^ 1
        

        #as_string = ''.join([hex(part) for part in parts]).replace('0x', r'\x')
        #print("Data parts as string: " + as_string)
        #return CRC16().calculate(as_string)


        #uint16_t joseta_calc_crc(uint8_t* data_p, uint8_t length){
        #uint8_t x;
        #uint16_t crc = 0; //0xFFFF;
        #while (length--){
        #        x = crc >> 8 ^ *data_p++;
        #        x ^= x>>4;
        #        crc = (crc << 8) ^ ((uint16_t)(x << 12)) ^ ((uint16_t)(x <<5)) ^ ((uint16_t)x);
        #}
        #return crc;

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

        # calculate CRC
        crc_raw = self._outgoing_crc(c)
        print("Found the CRC of " + str(crc_raw))
        crc_part1, crc_part2 = [ord(x) for x in struct.pack('H',crc_raw)]


        c.append(crc_part1) # CRC
        c.append(crc_part2) 
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
        c.append(0x00) # CRC
        c.append(0x00) 
        return c
        
    # process a command
    def _process(self, c):
    
        print("Incoming command: %s" % c)
        
        # data req
        if c[0] & 0xF0 == 0x10:
            curtime = int(time.time()) - self._time
            print("Current time is %d" % curtime)
            if c[1] & 0xF0 == 0xF0:
                for d in reversed(xrange(0,60)):
                    self._send(self._build_data(curtime - d))
            else:
                offset = (c[1] & 0x70) >> 4
                for d in xrange(0, 4):
                    self._send(self._build_data(curtime - 60 + offset + d))

        # ctrl set
        elif c[0] & 0xF0 == 0x20:
            pass
            
        # temp set
        elif c[0] & 0xF0 == 0x30:
            pass
            
        # time set or reset
        elif c[0] & 0xF0 == 0x40:
            
            # reset unit
            if c[1] & 0x80 == 0x00:
                time.sleep(1)
                self._send(self._build_init())
                
            # set time
            else:
                print("Epoch timestamp is %d" % (c[1] & 0x7F))
                self._time = int(time.time()) - (c[1] & 0x7F)
            
    # start command loop
    def start(self):
        while True:
            self._process(self._read())
        


if __name__ == "__main__":
    j = josetasim('/dev/ttyUSB0', 9600)
    j.start()

