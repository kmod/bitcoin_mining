import struct

H = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]
k = [
   0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
   0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
   0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
   0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
   0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
   0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
   0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
   0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
   ]

def precalc(preheader_bin):
    assert len(preheader_bin) == 76, len(preheader_bin)
    V = list(H)
    chunk(preheader_bin[:64], V)
    return V, preheader_bin[64:]

def finish_dsha(X, Y, nonce):
    V = list(X)
    # print "doing finish_dsha"
    chunk(Y + nonce + "\x80" + "\x00" * 45 + '\x02\x80', V)
    digest1 = struct.pack(">IIIIIIII", *V)
    # print hex(X[0])
    V = list(H)
    # print "doing second of finish_dsha"
    chunk(digest1 + "\x80" + "\x00" * 29 + "\x01\x00", V)
    digest2 = struct.pack(">IIIIIIII", *V)
    # print repr((X, Y, nonce))
    # raise Exception(struct.pack(">IIIIIIII", *X[::-1]).encode("hex"), Y[::-1].encode("hex"), nonce[::-1].encode("hex"), digest1[::-1].encode("hex"), digest2[::-1].encode("hex"))
    return digest2

def sha256(m):
    assert len(m) <= 2**32
    npad = (64 - 1 - 4 - len(m))
    npad = npad - 64 * (npad/64)
    assert npad >= 0
    m = m + '\x80' + '\x00' * npad + struct.pack(">I", len(m) * 8)
    # print repr(m)
    assert len(m) % 64 == 0, len(m)

    V = list(H)
    for i in xrange(0, len(m), 64):
        chunk(m[i:i+64], V)
    digest = struct.pack(">IIIIIIII", *V)
    return digest

def chunk(m, V):
    assert len(m) == 64, len(m)
    w = [struct.unpack(">I", m[i:i+4])[0] for i in xrange(0, 64, 4)]
    # print w
    assert len(w) == 16
    # print hex(w[0])

    def rightrotate(x, n):
        return (x >> n) + ((x << (32 - n)) & 0xffffffff)

    def rightshift(x, n):
        return x >> n

    for i in xrange(16, 64):
        s0 = rightrotate(w[i-15], 7) ^ rightrotate(w[i-15], 18) ^ rightshift(w[i-15], 3)
        s1 = rightrotate(w[i-2], 17) ^ rightrotate(w[i-2], 19) ^ rightshift(w[i-2], 10)
        t = (w[i-16] + s0 + w[i-7] + s1) & 0xffffffff
        w.append(t)

        # print "%08x %08x %08x %08x %08x" % (s0, s1, w[i-16], w[i-7], t)


    a,b,c,d,e,f,g,h = V
    for i in xrange(0, 64):
        s1 = rightrotate(e, 6) ^ rightrotate(e, 11) ^ rightrotate(e, 25)
        ch = (e & f) ^ ((~e) & g)
        temp1 = (h + s1 + ch + k[i] + w[i]) & 0xffffffff
        s0 = rightrotate(a, 2) ^ rightrotate(a, 13) ^ rightrotate(a, 22)
        maj = (a & b) ^ (a & c) ^ (b & c)
        temp2 = (s0 + maj) & 0xffffffff

        h = g
        g = f
        f = e
        e = (d + temp1) & 0xffffffff
        d = c
        c = b
        b = a
        a = (temp1 + temp2) & 0xffffffff

        if 0:
            print "%08x %08x %08x %08x %08x %08x %08x %08x" % (a, b, c, d, e, f, g, h),
            print "| %08x %08x %08x %08x %08x %08x %08x %08x" % (s1, ch, temp1, s0, maj, temp2, k[i], w[i])

    V[0] = (V[0] + a) & 0xffffffff
    V[1] = (V[1] + b) & 0xffffffff
    V[2] = (V[2] + c) & 0xffffffff
    V[3] = (V[3] + d) & 0xffffffff
    V[4] = (V[4] + e) & 0xffffffff
    V[5] = (V[5] + f) & 0xffffffff
    V[6] = (V[6] + g) & 0xffffffff
    V[7] = (V[7] + h) & 0xffffffff
    # print hex(V[0])
    return V

def _test(s):
    import hashlib
    assert sha256(s) == hashlib.sha256(s).digest()
if __name__ == "__main__":
    _test("abc")
    _test("abc")
    _test("abc" * 30)
    print sha256("abc")[::-1].encode("hex")


# for i in xrange(64):
    # b = bin(i)[2:].rjust(6, '0')
    # h = hex(k[i])[2:].rjust(8, '0')
    # print "case 6'b%s: k = 32'h%s;" % (b, h)
# print ''.join([hex(x)[2:] for x in reversed(H)])
