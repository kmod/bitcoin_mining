import threading
import os
import binascii
import hashlib
try:
    import simplejson
except ImportError:
    import json as simplejson
import socket
import struct
import sys
import time
import traceback

TEST = 0
THRESH = 1

from util import RecentCache
import sha

def doublesha(d):
    return hashlib.sha256(hashlib.sha256(d).digest()).digest()

def finish_dsha(sha_obj, end):
    sha_obj = sha_obj.copy()
    sha_obj.update(end)
    # return sha.sha256(sha_obj.digest())
    return hashlib.sha256(sha_obj.digest()).digest()

def build_merkle_root(merkle_branch, coinbase_hash_bin):
    merkle_root = coinbase_hash_bin
    for h in merkle_branch:
        merkle_root = doublesha(merkle_root + binascii.unhexlify(h))
    return merkle_root

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

class JobInfo(object):
    def __init__(self, extranonce1, id, prevhash, coinb1, coinb2, merkle_branch, version, nbits, ntime):
        self.extranonce1 = extranonce1
        self.id = id
        self.prevhash = prevhash
        self.coinb1 = coinb1
        self.coinb2 = coinb2
        self.merkle_branch = merkle_branch
        self.version = version
        self.nbits = nbits
        self.ntime = ntime

    def verify(self, extranonce2, ntime, nonce):
        coinbase = self.coinb1 + self.extranonce1 + extranonce2 + self.coinb2
        coinbase_hash_bin = doublesha(binascii.unhexlify(coinbase))
        merkle_root = build_merkle_root(self.merkle_branch, coinbase_hash_bin)
        merkle_root = ser_uint256_be(uint256_from_str(merkle_root))
        preheader = self.version + self.prevhash + merkle_root.encode("hex") + ntime + self.nbits
        preheader_bin = preheader.decode("hex")
        preheader_bin = ''.join([preheader_bin[i*4:i*4+4][::-1] for i in range(0,19)])

        hash_bin = doublesha(preheader_bin + nonce.decode("hex")[::-1])
        print hash_bin.encode("hex")
        val = struct.unpack("<I", hash_bin[-4:])[0]
        assert val < THRESH

class StratumClient(object):
    def __init__(self, f):
        self.mid = 3
        self.done = False

        self.f = f
        self.f.write("""{"id": 1, "method": "mining.subscribe", "params": []}\n""")
        self.f.write("""{"id": 2, "method": "mining.authorize", "params": ["kmod_3", "123"]}\n""")
        self.f.flush()

        self.w = None
        self.jobs = RecentCache(n=1000)

    def run(self):
        while True:
            s = self.f.readline()
            if not s:
                break

            if TEST:
                s = """{"params": ["bf", "4d16b6f85af6e2198f44ae2a6de67f78487ae5611b77c6c0440b921e00000000",
        "01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff20020862062f503253482f04b8864e5008",
        "072f736c7573682f000000000100f2052a010000001976a914d23fcdf86f7e756a64a7a9688ef9903327048ed988ac00000000", [],
        "00000002", "1c2ac4af", "504e86b9", false], "id": null, "method": "mining.notify"}"""
                extranonce1 = "08000002"

            s = s.strip()
            assert s
            d = simplejson.loads(s)

            if d.get('method', None) == "mining.notify" and self.done:
                continue

            print d

            if d.get('error', None):
                raise Exception()

            if d['id'] == 1 and 'method' not in d:
                subscription, extranonce1, extranonce2_size = d['result']

            elif d.get('method', None) == "mining.set_difficulty":
                assert d['params'] == [1]

            elif d.get('method', None) == "mining.notify":
                if self.w:
                    print "stopping existing worker"
                    self.w.stop()

                params, clean_jobs = d['params'][:-1], d['params'][:-1]
                j = JobInfo(extranonce1, *params)
                self.jobs[j.id] = j

                extranonce2 = ((int(time.time()) << 16) + os.getpid()) & 0xffffffff
                extranonce2 = struct.pack(">I", extranonce2).encode("hex")
                if TEST:
                    extranonce2 = "00000001"
                print extranonce2

                coinbase = j.coinb1 + extranonce1 + extranonce2 + j.coinb2
                coinbase_hash_bin = doublesha(binascii.unhexlify(coinbase))
                merkle_root = build_merkle_root(j.merkle_branch, coinbase_hash_bin)
                merkle_root = ser_uint256_be(uint256_from_str(merkle_root))

                # ntime = "504e86ed"
                ntime = j.ntime
                if TEST:
                    ntime = "504e86ed"

                preheader = j.version + j.prevhash + merkle_root.encode("hex") + ntime + j.nbits
                preheader_bin = preheader.decode("hex")
                preheader_bin = ''.join([preheader_bin[i*4:i*4+4][::-1] for i in range(0,19)])

                self.w = CpuWorker(self)
                self.w.start(j.id, extranonce2, ntime, preheader_bin)

            else:
                assert d['id'] < self.mid

    def submit(self, job_id, extranonce2, ntime, nonce):
        print "SUBMITTING"
        cmd = """{"params": ["kmod_3", "%s", "%s", "%s", "%s"], "id": %d, "method":"mining.submit"}\n""" % (job_id, extranonce2, ntime, nonce, self.mid)
        print cmd
        j = self.jobs[job_id]

        j.verify(extranonce2, ntime, nonce)

        self.f.write(cmd)
        self.f.flush()
        self.mid += 1
        self.done = True

class WorkerBase(object):
    def __init__(self, cl):
        self._cl = cl
        self._quit = False
        self._done_ev = threading.Event()

    def start(self, job_id, extranonce2, ntime, preheader_bin):
        t = threading.Thread(target=self._target, args=(job_id, extranonce2, ntime, preheader_bin))
        t.setDaemon(True)
        t.start()

    def stop(self):
        self._quit = True
        self._done_ev.wait()

class CpuWorker(WorkerBase):
    def _target(self, job_id, extranonce2, ntime, preheader_bin):
        try:
            start = time.time()

            first_sha = hashlib.sha256(preheader_bin)

            if sys.maxint > 2**32:
                max_nonce = 2**32
            else:
                max_nonce = 2**31 - 1
            i = 0
            while i < max_nonce:
                if i % 100000 == 0:
                    print i, "%.1f kh/s" % (i * .001 / (time.time() - start + .001))
                    if self._quit:
                        print "QUITTING WORKER"
                        break

                nonce_bin = struct.pack(">I", i)
                if TEST:
                    nonce_bin = "b2957c02".decode("hex")[::-1]

                # header_bin = preheader_bin + nonce_bin
                # hash_bin = doublesha(header_bin)
                # assert hash_bin == finish_dsha(first_sha, nonce_bin)
                hash_bin = finish_dsha(first_sha, nonce_bin)

                val = struct.unpack("<I", hash_bin[-4:])[0]
                if val < THRESH:
                    nonce = nonce_bin[::-1].encode("hex")
                    print nonce, extranonce2, ntime
                    print hash_bin.encode("hex")
                    hash_int = uint256_from_str(hash_bin)
                    block_hash_hex = "%064x" % hash_int
                    print block_hash_hex


                    self._cl.submit(job_id, extranonce2, ntime, nonce)
                    break
                elif val < THRESH*10:
                    print "almost: %d (<%d)" % (val, THRESH)
                i += 1
                # elif i == 0:
                    # print hash_bin.encode("hex")
            self._done_ev.set()
        except:
            traceback.print_exc()
            os._exit(1)

if __name__ == "__main__":
    sock = socket.socket()
    sock.connect(("stratum.btcguild.com", 3333))


    StratumClient(sock.makefile()).run()
    f = sock.makefile()
