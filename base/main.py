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
        
print("[ds] Init poller")
pol = poller(None, delay=5, interval=60)

print("[ds] Init plotter")
plo = plotter('demo.pdf', interface.PKT_FIELDS, 'timesta')

print("[ds] Init interface")
d = interface('/dev/ttyACM1', '\x1b\x63', callback_factory(pol, plo), slaves=['d5d9'])
pol.transport = d

print("[ds] Start poll thread")
pol.start()

print("[ds] Start interface")
d.start()

print("[ds] Start plotter")
plo.plot_loop()
print("[ds] Plotter stopped")

print("[ds] Stopping poller")
pol.stop()

print("[ds] Stopping interface")
d.stop()

print("[ds] Terminating")
