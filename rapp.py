import struct

class rapp_pkt:

    type_code = { 0x01 : 'Q',
                  0x02 : 'q',
                  0x03 : 'I',
                  0x04 : 'i',
                  0x05 : 'H',
                  0x06 : 'h',
                  0x07 : 'B',
                  0x08 : 'b',
                  0x11 : 'd',
                  0x12 : 'f',
                  0x21 : '8s',
                  0x22 : '4s',
                  0x23 : '2s'
                }
                
    type_size = { 0x01 : 8,
                  0x02 : 8,
                  0x03 : 4,
                  0x04 : 4,
                  0x05 : 2,
                  0x06 : 2,
                  0x07 : 1,
                  0x08 : 1,
                  0x11 : 8,
                  0x12 : 4,
                  0x21 : 8,
                  0x22 : 4,
                  0x23 : 2
                }
                
    def __init__(self, raw):
        self.raw = raw
        self.parse_raw()
        
    def parse_raw(self):
        self.parsed = []
        self.names = []
        offset = 0
        
        # read first two bytes of header
        (sset_ct, samp_ct) = struct.unpack("<BB", self.raw[0:2])
        offset = 2
        
        print("expecting %d sets of %d samples" % (sset_ct, samp_ct))
        
        # read names
        for i in range(0, samp_ct):
            self.names.append(self.raw[offset:offset+8].rstrip('\x00'))
            offset += 8
            print("field name: %s" % (self.names[len(self.names)-1]))
            
        # begin reading sample sets
        for i in range(0, sset_ct):
            current = {}
            for j in range(0, samp_ct):
                vtype = struct.unpack("<B", self.raw[offset])[0]
                print("reading value of type %02x" % vtype)
                offset += 1
                fmt = "<%s" % rapp_pkt.type_code[vtype]
                length = rapp_pkt.type_size[vtype]
                print("format is %s, len is %d" % (fmt, length))
                value = struct.unpack(fmt, self.raw[offset:offset+length])[0]
                print("value is %s" % value)
                offset += length
                current[self.names[j]] = value
            self.parsed.append(current)
         
        return self.parsed

