import struct

class RecentCache(object):
    """
    very simple LRU-ish cache
    """
    def __init__(self, n):
        self.d1 = {}
        self.d2 = {}
        self._n = n

    def __setitem__(self, k, v):
        # print k, v
        self.d1[k] = v
        self.d2.pop(k, None)
        if len(self.d1) >= self._n:
            self.d2 = self.d1
            self.d1 = {}

    def __getitem__(self, k):
        if k in self.d1:
            return self.d1[k]
        return self.d2[k]

def uint256_from_str(s):
    r = 0L
    t = struct.unpack("<IIIIIIII", s[:32])
    for i in xrange(8):
        r += t[i] << (i * 32)
    return r
def ser_uint256_be(u):
    '''ser_uint256 to big endian'''
    rs = ""
    for i in xrange(8):
        rs += struct.pack(">I", u & 0xFFFFFFFFL)
        u >>= 32
    return rs    

