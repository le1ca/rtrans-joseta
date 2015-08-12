#!/usr/bin/env python
from interface import * 
from poller import * 
from plotter import * 

from sys import argv

def transpose(series):
        n = {}
        for x in series:
                for y in x:
                        if not y in n:
                                n[y] = []
                        n[y].append(x[y])
        return n


def callback_factory(poll, plot):
        poller  = poll
        plotter = plot
        
        def callback(event, arg):
                if event == 'join':
                        poller.register_slave(arg)
                elif event == 'data':
                        plotter.make_plot(transpose(arg))
                        
        return callback
        
print("init poller")
pol = poller(None, delay=5, interval=60)

print("init plotter")
plo = plotter('demo.pdf', interface.PKT_FIELDS, 'timesta')

print("init interface")
d = interface('/dev/ttyUSB0', '\x1b\x63', callback_factory(pol, plo), slaves=['d5d9'])
pol.transport = d

print("start poll thread")
pol.start()

print("start interface")
d.start()

print("terminating")
