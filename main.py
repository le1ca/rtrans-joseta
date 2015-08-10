#!/usr/bin/env python

# Xbee Transport
# Base station implementation

import time
from rtrans import rt
from rapp import rapp_pkt
from sys import argv, stdout
from struct import unpack

sim_loss=0

PKT_FIELDS = ["timesta", "occupan", "relay", "voltage", "current", "phase", "tempera"]
PKT_TYPES = {
        'timesta': 'lu',
        'voltage': 'u',
        'current': 'u',
        'phase':   'd',
        'tempera': 'd',
        'occupan': 'd',
        'relay':   'd'
}
        
def cb(s, t, p):
    if t == rt.ptype['DATA']:
        print("Data from %04x:" % s)
        if len(p) > 0:
                data = rapp_pkt(p)
                for v in data.parsed:
                    for field in PKT_FIELDS:
                        stdout.write(("%%s=%%%s, " % PKT_TYPES[field]) % (field, v[field]))
                    stdout.write("\b\b  \n")
                transport._continue = False
        else:
                print("discarding 0-length packet")
    elif t == rt.ptype['JOIN']:
        print("Join from %04x." % (s))
        transport.poll(s)

# NOTE TO SELF:
# =============================================================================
# CONFIGURE THE XBEE WITH ATAP1 AND ATMM2 OR YOU WILL WASTE TWO DAYS DEBUGGING
# SET ATMY TO THE LOW TWO BYTES OF ATDL THEN COPY IT BELOW
# THE TWO-BYTE ADDRESS HERE IS WITH THE REVERSE ENDIANNESS OF THE XBEE ITSELF
# OR JUST IMPLEMENT A CONFIGURATION ROUTINE YOU LAZY BASTARD

transport = rt("/dev/ttyUSB1", 9600, '\x1b\x63', cb, sim_loss, 0.5)
#transport = rt("/dev/ttyUSB1", 9600, '\xff\xff', cb, sim_loss, 0.5)
if len(argv) > 1:
        for slave in argv[1:]:
                print("Manually adding slave %s" % slave)
                transport.add_slave(unpack(">H", slave.decode('hex'))[0])
transport.probe()
transport.wait()
