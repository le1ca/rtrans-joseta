#!/usr/bin/env python

# Xbee Transport
# Base station implementation

import time
from rtrans import rt

sim_loss=0
        
def cb(s, t, p):
    if t == rt.ptype['DATA']:
        print("Data from %04x:\n%s\n" % (s, p))
    elif t == rt.ptype['JOIN']:
        print("Join from %04x." % (s))
        transport.poll(s)

transport = rt("/dev/ttyUSB1", 9600, '\x18\x4c', cb, sim_loss)
transport.probe()
transport.wait()
