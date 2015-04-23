#!/usr/bin/env python

# Xbee Transport
# Base station implementation

import time
from rtrans import rt

sim_loss=0.6
        
def cb(s, t, p):
    print("Package from %04x of type %02x:\n%s\n" % (s, t, p))

transport = rt("/dev/ttyUSB1", 9600, '\x18\x4c', cb, sim_loss)
transport.probe()
transport.wait()
