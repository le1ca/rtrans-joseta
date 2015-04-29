#!/usr/bin/env python

# Xbee Transport
# Base station implementation

import time
from rtrans import rt
from rapp import rapp_pkt

sim_loss=0
        
def cb(s, t, p):
    if t == rt.ptype['DATA']:
        print("Data from %04x:" % s)
        data = rapp_pkt(p)
        for v in data.parsed:
            print("time=%lu, voltage=%u, current=%u, temp=%d" % (v['timesta'], v['voltage'], v['current'], v['tempera']))
    elif t == rt.ptype['JOIN']:
        print("Join from %04x." % (s))
        transport.poll(s)

transport = rt("/dev/ttyUSB1", 9600, '\x18\x4c', cb, sim_loss, 0.5)
transport.probe()
transport.wait()
