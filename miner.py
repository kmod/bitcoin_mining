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
WORKER_NAME = "kmod.kmod1"
WORKER_PW = os.environ["WORKER_PW"]

from util import RecentCache, ser_uint256_be, uint256_from_str

def doublesha(d):
    return hashlib.sha256(hashlib.sha256(d).digest()).digest()

def build_merkle_root(merkle_branch, coinbase_hash_bin):
    merkle_root = coinbase_hash_bin
    for h in merkle_branch:
        merkle_root = doublesha(merkle_root + binascii.unhexlify(h))
    return merkle_root

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
        return
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
        assert val < THRESH, (val, THRESH)

class StratumClient(object):
    def __init__(self, f, worker_cls):
        self.mid = 3
        self.nfound = 0

        self.f = f
        self.f.write("""{"id": 1, "method": "mining.subscribe", "params": []}\n""")
        self.f.write("""{"id": 2, "method": "mining.authorize", "params": ["%s", "%s"]}\n""" % (WORKER_NAME, WORKER_PW))
        self.f.flush()

        self.jobs = RecentCache(n=1000)

        self.w = worker_cls(self)

    def run(self):
        difficulty = 1
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

            # if d.get('method', None) == "mining.notify" and self.done:
                # continue

            print d

            if d.get('error', None):
                raise Exception()

            if d['id'] == 1 and 'method' not in d:
                subscription, extranonce1, extranonce2_size = d['result']

            elif d.get('method', None) == "mining.set_difficulty":
                difficulty = d['params'][0]

            elif d.get('method', None) == "mining.notify":
                print "stopping worker"
                self.w.stop()
                print "stopped"

                params, clean_jobs = d['params'][:-1], d['params'][:-1]
                j = JobInfo(extranonce1, *params)
                self.jobs[j.id] = j

                extranonce2 = ((int(time.time()) << 16) + os.getpid()) & 0xffffffff
                extranonce2 = struct.pack(">I", extranonce2).encode("hex")
                if TEST:
                    extranonce2 = "00000001"
                print "extranonce2 = %s" % extranonce2

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

                self.w.start(difficulty, j.id, extranonce2, ntime, preheader_bin)

            else:
                assert d['id'] < self.mid

    def submit(self, job_id, extranonce2, ntime, nonce):
        print "SUBMITTING"
        cmd = """{"params": ["%s", "%s", "%s", "%s", "%s"], "id": %d, "method":"mining.submit"}\n""" % (WORKER_NAME, job_id, extranonce2, ntime, nonce, self.mid)
        print cmd
        j = self.jobs[job_id]

        j.verify(extranonce2, ntime, nonce)

        self.f.write(cmd)
        self.f.flush()
        self.mid += 1
        self.nfound += 1

if __name__ == "__main__":
    sock = socket.socket()
    sock.connect(("stratum.slushpool.com", 3333))
    # sock.connect(("coins.arstechnica.com", 3333))

    from sha_mining import CpuWorker, FPGAWorker
    # from scrypt_mining import CpuWorker

    worker_cls = CpuWorker
    if len(sys.argv) >= 2:
        if sys.argv[1] == "fpga":
            worker_cls = FPGAWorker

    StratumClient(sock.makefile(), worker_cls).run()
    f = sock.makefile()
