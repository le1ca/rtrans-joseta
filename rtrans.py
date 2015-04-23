#!/usr/bin/env python

from rt_pkt import rt_pkt
from serial import Serial
from xbee import XBee
import time, struct, threading, random
        
# transport layer implementation
class rt:

    # type field constants
    ptype = { 'ACK':   254,
              'NAK':   255,
              'PROBE': 0,
              'JOIN':  1,
              'POLL':  2,
              'DATA':  3,
              'SET':   4,
              'ERR':   5
            }

    def __init__(self, tty, baud, addr, callback, loss=0.0):
        self.tty  = Serial(tty, baudrate=baud)
        self.xbee = XBee(self.tty, callback=self._recv_frame)
        self.addr = struct.unpack("<H", addr)[0]
        self._frame = 0
        self._data = {}
        self._timer = {}
        self._callback = callback
        self._loss = loss
    
    def _send(self, dest, pkg_type, pkg_no, seg_ct, seg_no, payload):
        rp = { 'master':   self.addr,
               'slave':    dest,
               'pkg_no':   pkg_no,
               'pkg_type': pkg_type,
               'seg_ct':   seg_ct,
               'seg_no':   seg_no,
               'payload':  payload
             }
        if random.random() > self._loss:
            self.xbee.tx(dest_addr=struct.pack(">H", dest), data=rt_pkt(parms=rp).raw)

    def _ack(self, pkt):
        self._send(pkt['slave'], rt.ptype['ACK'], pkt['pkg_no'], 1, pkt['seg_no'], "")
    
    def send(self, dest, pkg_type, payload):
        self._send(dest, pkg_type, self._frame, 1, 0, payload)
        self._frame += 1
        
    def wait(self):
        while True:
            try:
                time.sleep(0.1)
            except KeyboardInterrupt:
                self._end()
                time.sleep(0.1)
                break
                
    def _ptimer(self, pid):
        if pid in self._timer:
            self._timer[pid].cancel()
        self._timer[pid] = threading.Timer(5.0, rt._expire, [self, pid])
        self._timer[pid].start()
                
    def _expire(self, pid):
        del self._data[pid]
        del self._timer[pid]
        
    def _recv_frame(self, x):
        if x['id'] == 'rx':
            if random.random() > self._loss:
                self._proc_frame(x)
        
    def _proc_frame(self, x):  
        if x['id'] == 'rx':
            # parse incoming packet
            pkt = rt_pkt(raw=x['rf_data'])
                    
            # ack the packet
            self._ack(pkt)                    
                    
            # if the packet was a join, poll the node for data
            if pkt['pkg_type'] == rt.ptype['JOIN']:
                self.send(pkt['slave'], rt.ptype['POLL'], "")
                        
            # handle data packet
            elif pkt['pkg_type'] == rt.ptype['DATA']:
                pid = (pkt['slave'], pkt['pkg_no'])
                
                # check if we were waiting for this slave's data
                if pkt['seg_no'] == 0 and pkt['slave']:
                    # TODO
                    pass
                
                # add segment to the corresponding buffer and call the callback if it is complete
                if pkt['seg_no'] == 0 and pkt['seg_ct'] == 1:
                    self._callback(pkt['slave'], pkt['pkg_type'], pkg['payload'])
                elif pkt['seg_no'] == 0:
                    self._data[pid] = [pkt]
                    self._ptimer(pid)
                elif pid in self._data:
                    self._timer[pid].cancel()
                    l = self._data[pid]
                    if l[len(l)-1]['seg_no'] == pkt['seg_no'] - 1:
                        l.append(pkt)
                        if pkt['seg_no'] == pkt['seg_ct'] - 1:
                            payload = "".join([pp['payload'] for pp in l])
                            self._callback(pkt['slave'], pkt['pkg_type'], payload)
                            del self._data[pid]
                else:
                    print("[rt] unexpected segment %04x.%02x" % (pkt['pkg_no'], pkt['seg_no']))
                
    def probe(self):
        self.send(0xffff, rt.ptype['PROBE'], "")
    
    def _end(self):    
        self.xbee.halt()
        self.tty.close()

