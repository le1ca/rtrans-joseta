""" 
Goal: have radio1 act as the base station, radio2 as a slave.
Radio1 polls, radio2 responds with its address, radio1 adds it to the list of slaves.
Then every X seconds, radio1 polls all its slaves to get new data.
"""

from xbee import XBee, ZigBee
from serial import Serial
import serial, time

from rtrans import rt
from rt_slave import rt_slave

"""
HIERARCHY OF FUNCTIONS (as many of them are abstractions / wrappings of others)

LEVEL 0:
ser.write(msg) sends msg to the xbee.
ser.read(number_of_bytes) reads some characters.

LEVEL 1:
xbee_clear_buffer() reads and throws away everything in the XBee read buffer.
xbee_wait_for_ok() reads 3 characters, and returns true if there was an "OK\r" returned by the XBee.

LEVEL 2:
xbee_command(ser, msg) clears the buffer, sends the msg to the xbee, then waits for an OK. Do not include a \r - xbee_command takes care of that for you.
xbee_request(ser, msg) same as xbee_command, but returns the XBee's response.

LEVEL 3:
xbee_set_my()
xbee_factory_reset()
xbee_set_destination()
xbee_enter_command_mode(ser): enters command mode.
xbee_exit_command_mode(ser): exits command mode.

LEVEL 4:
X xbee_configure() puts the xbee in command mode, executes some commands, and exits command mode.
xbee_two_way_setup(xs1, xs2) puts two XBees in communication with each other.
xbee_api_mode(ser)
"""

import struct

def xbee_clear_buffer(xs):
    """Clears the read buffer.
    Optionally returns what it read.
    """
    buffer = []
    while xs.inWaiting():
        buffer.append(xs.read())
    return ''.join(buffer)

def xbee_wait_for_ok(xs):
    okcr = 'OK\r'
    err = False
    c = xs.read(3)
    # print ('RESPONSE: %s' %c)
    if c != okcr:
        err = True

    return not err

def xbee_request(xs, request):
    """
    Similar to xbee_command, except this function waits for information
    instead of an 'OK\r' response.

    Returns the response with the trailing '\r' excluded. 
    If the request was actually a command (i.e. ATMY0), 
    then the response will be 'OK'. 
    If there was an error, the response will be 'ERROR'.
    """

    xbee_clear_buffer(xs)
    xs.write(request + '\r')
    # print("Requested " + request)
    
    # Any response will end with \r - that is how we know where it ends
    response_chars = ['']
    while response_chars[-1] != '\r':
        ch = xs.read()
        # print("Got a char: " + repr(ch))
        response_chars.append(ch)
    return ''.join(response_chars[:-1])
        
def xbee_command(xs, command):
    """
    The \r is added because there is no scenario in which a person wants to A) wait for an OK\r but 
    B) not want a carriage return EXCEPT when when entering command mode, which is already covered in
    xbee_enter_command_mode().
    """
    xbee_clear_buffer(xs)

    # print ('SEND: %s' % command)
    xs.write(command + '\r')
    return xbee_wait_for_ok(xs)
    
def xbee_enter_command_mode(xs):
    xbee_clear_buffer(xs)
    xs.write('+++')
    return xbee_wait_for_ok(xs)
    
def xbee_exit_command_mode(xs):
    return xbee_command(xs, 'ATCN')

def xbee_factory_reset(xs):
    ok = True
    ok &= xbee_command(xs, 'ATRE')
    ok &= xbee_command(xs, 'ATWR')
    ok &= xbee_command(xs, 'ATFR')
    return ok

def xbee_set_my(xs):
    """
    Sets the MY (unique ID) of the xbee to the lower byte of its unique
    serial number.
    """
    serial_number_low = xbee_request(xs, 'ATSL')
    # MY can only be 16 bits, so get the last 4 chars, which are in hex
    xbee_command(xs, 'ATMY' + serial_number_low[-4:])
    
def xbee_set_destination(xs_sender, xs_recipient):
    """
    Tells xs_sender to send to xs_recipient.
    
    Sets the "destination" byte (DL, or Destination Low) in xs_sender
    to the MY address of xs_recipient.
    Usually you'd want to run this twice, with arguments reversed, to get radios to talk to each other.
    """
    
    recipient_addr = xbee_request(xs_recipient, 'ATMY')
    return xbee_command(xs_sender, 'ATDL' + recipient_addr)
    
def xbee_two_way_setup(xs1, xs2):
    ok = True
    
    ok_responses = [
        xbee_enter_command_mode(xs1),
        xbee_enter_command_mode(xs2),
    
        xbee_set_my(xs1),
        xbee_set_my(xs2),
    
        xbee_set_destination(xs1, xs2),
        xbee_set_destination(xs2, xs1),
    
        xbee_exit_command_mode(xs1),
        xbee_exit_command_mode(xs2)
    ]

    return all(ok_responses)

"""
Puts the XBee into API mode.
"""
def xbee_api_mode(xs):
   commands = [
      'ATCH0C',
      'ATID3332',
      'ATAP1',
      'ATAC',
   ]
   
   ok = xbee_enter_command_mode(xs)

   for cmd in commands:
      ok &= xbee_command(xs, cmd)

   ok &= xbee_exit_command_mode(xs)

   time.sleep(1)

   return ok

#xbee_init(xs)

def two_way_api_mode_example():
    """radio1 = XBee(ser = serial.Serial('/dev/ttyAMA0', 9600),
                  callback = lambda *_, **__: None,
                  escaped = True
                 )
    radio2 = XBee(ser = serial.Serial('/dev/ttyUSB0', 9600),
                  callback = lambda *_, **__: None,
                  escaped = True
                 )"""
    radio1 = Serial('/dev/ttyAMA0', 9600)
    radio2 = Serial('/dev/ttyUSB0', 9600)
    
    
    """xbee_two_way_setup(radio1, radio2)
    radio1.write("abcdefg")
    time.sleep(1)
    print(repr(xbee_clear_buffer(radio2)))"""
    
    """ok = True
    print("A")
    ok &= xbee_two_way_setup(radio1, radio2)
    print("B")
    ok &= xbee_api_mode(radio1)
    print("C")
    ok &= xbee_api_mode(radio2)
    print(ok)"""
    
    # Assume they are in API mode
    def arbitrary_printer(*args, **kwargs):
        print("Args: " + str(args))
        print("Kwargs: " + str(kwargs))

    ama0 = rt(      tty='/dev/ttyAMA0', baud=9600, addr='\xD9\xD5', callback=arbitrary_printer)
    usb0 = rt_slave(tty='/dev/ttyUSB0', baud=9600, addr='\xD4\x75', callback=arbitrary_printer)

    ama0.probe()
    time.sleep(5)
    
def remote_api_mode_test():
    radio1 = Serial('/dev/ttyAMA0', 9600)
    
    def arbitrary_printer(*args, **kwargs):
        print("Args: " + str(args))
        print("Kwargs: " + str(kwargs))

    ama0 = rt(tty='/dev/ttyAMA0', 
              baud=9600, 
              addr='\xD9\xD5',
              callback=arbitrary_printer)

    print("Set up the rt object")
    ama0.probe()

def interest_test():
    radio1 = Serial('/dev/ttyAMA0', 9600)
    
    def arbitrary_printer(*args, **kwargs):
        print("Args: " + str(args))
        print("Kwargs: " + str(kwargs))

    ama0 = rt(tty='/dev/ttyAMA0', 
              baud=9600, 
              addr='\xD9\xD5',
              callback=arbitrary_printer)

    interest_msg = "Q"
    #ama0.xbee.tx(dest=struct.pack(">H", 0xFFFF), data=interest_msg)
    ama0.send(0xffff, rt.ptype['PROBE'], "Q")
   


if __name__ == "__main__":
    interest_test()

"""
if __name__ == "__main__":
        # interface('/dev/ttyUSB0', '\x1b\x63', callback_factory(pol, plo), slaves=['d5d9'])
        radio1 = interface(tty="/dev/ttyAMA0", addr='\x00\x00', cb=callback_producer("from_00_to_01"), slaves=['0001'], options={"probe_interval": 3})
        # self.send(0xffff, rt.ptype['PROBE'], "")  # rt.ptype['PROBE'] is 0
        # def send(self, dest, pkg_type, payload):
        #       self._send(dest, pkg_type, self._frame, 1, 0, payload)
        #       self._frame += 1
        # =
        # self._send(0xffff, rt.ptype['PROBE'], self._frame, 1, 0, "")
        # def _send(self, dest, pkg_type, pkg_no, seg_ct, seg_no, payload):
        #       rp = { 'master':   self.addr,
        #              'slave':    dest,
        #              'pkg_no':   pkg_no,
        #              'pkg_type': pkg_type,
        #              'seg_ct':   seg_ct,
        #              'seg_no':   seg_no,
        #              'payload':  payload
        #       }
        #       self.xbee.tx(dest_addr=struct.pack(">H", dest), data=rt_pkt(parms=rp).raw)
        # self.xbee.tx(dest_addr=struct.pack(">H", 0xffff), data=
        # radio1.start()
        # XBee(self.tty, callback=self._recv_frame, escaped=True)

        radio1.transport.xbee.tx(dest_addr="\x00\x01", data="Hello")
        radio2 = interface(tty="/dev/ttyUSB0", addr='\x00\x01', cb=callback_producer("from_01_to_00"), slaves=['0000'])
        radio2.transport.xbee.tx(dest_addr="\x00\x00", data="Goodbye")

        #from xbee import XBee
        #xb1 = XBee("/dev/ttyAMA0", callback=callback_producer("uno"), escaped=True)
        #xb2 = XBee("/dev/ttyUSB0", callback=callback_producer("dos"), escaped=True)
        #xb2.tx(dest_addr="\x00\x00", data="Hello?")
        #print("Sent")

        xb1 = 
"""
