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

m = '\x61\x62\x63\x80' + '\x00' * 59 + '\x18'
assert len(m) == 64
w = [struct.unpack(">I", m[i:i+4])[0] for i in xrange(0, 64, 4)]
print w
assert len(w) == 16
print hex(w[0])

def rightrotate(x, n):
    return (x >> n) + ((x << (32 - n)) & 0xffffffff)

def rightshift(x, n):
    return x >> n

for i in xrange(16, 64):
    s0 = rightrotate(w[i-15], 7) ^ rightrotate(w[i-15], 18) ^ rightshift(w[i-15], 3)
    s1 = rightrotate(w[i-2], 17) ^ rightrotate(w[i-2], 19) ^ rightshift(w[i-2], 10)
    t = (w[i-16] + s0 + w[i-7] + s1) & 0xffffffff
    w.append(t)


a,b,c,d,e,f,g,h = H
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

    print "%08x %08x %08x %08x %08x %08x %08x %08x" % (a, b, c, d, e, f, g, h)

H[0] = (H[0] + a) & 0xffffffff
H[1] = (H[1] + b) & 0xffffffff
H[2] = (H[2] + c) & 0xffffffff
H[3] = (H[3] + d) & 0xffffffff
H[4] = (H[4] + e) & 0xffffffff
H[5] = (H[5] + f) & 0xffffffff
H[6] = (H[6] + g) & 0xffffffff
H[7] = (H[7] + h) & 0xffffffff
digest = struct.pack(">IIIIIIII", *H)
print digest.encode("hex")
