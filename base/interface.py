#!/usr/bin/env python

# Xbee Transport
# Base station implementation

import time
from rtrans import rt
from rapp import rapp_pkt
from sys import argv, stdout
from struct import unpack

class interface:

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
        
        def __init__(self, tty, addr, cb, slaves=[], options={}):
                self.data = []
                self.cb = cb
                self.transport = rt(tty, 9600, addr, self._cb, **options)
                for slave in slaves:
                        print("Manually adding slave %s" % slave)
                        self.transport.add_slave(unpack(">H", slave.decode('hex'))[0])
        
        def start(self):
               self.transport.probe()
               self.transport.wait()
       
        def poll(self, addr):
                self.transport.poll(addr)
        
        def _cb(self, s, t, p):
            if t == rt.ptype['DATA']:
                print("Data from %04x:" % s)
                if len(p) > 0:
                        data = rapp_pkt(p)
                        for v in data.parsed:
                            self.data.append(v)
                            #for field in PKT_FIELDS:
                            #    stdout.write(("%%s=%%%s, " % PKT_TYPES[field]) % (field, v[field]))
                            #stdout.write("\b\b  \n")
                        self.cb('data', self.data)
            elif t == rt.ptype['JOIN']:
                print("Join from %04x." % (s))
                #transport.poll(s)
                self.cb('join', s)

