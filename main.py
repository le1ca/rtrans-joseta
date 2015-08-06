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
        if len(p) > 0:
                data = rapp_pkt(p)
                for v in data.parsed:
                    print("time=%lu, voltage=%u, current=%u, temp=%d" % (v['timesta'], v['voltage'], v['current'], v['tempera']))
        else:
                print("discarding 0-length packet")
    elif t == rt.ptype['JOIN']:
        print("Join from %04x." % (s))
        transport.poll(s)

# NOTE TO SELF:
# =============================================================================
# CONFIGURE THE XBEE WITH ATAP1 AND ATMM2 OR YOU WILL WASTE TWO DAYS DEBUGGING
# SET ATMY TO THE LOW BYTE OF ATDL THEN COPY IT BELOW
# THE TWO-BYTE ADDRESS HERE IS WITH THE REVERSE ENDIANNESS OF THE XBEE ITSELF
# OR JUST IMPLEMENT A CONFIGURATION ROUTINE YOU LAZY BASTARD

transport = rt("/dev/ttyUSB1", 9600, '\x1b\x63', cb, sim_loss, 0.5)
transport.probe()
transport.wait()
