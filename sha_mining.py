import traceback
import os
import sys
import time
import hashlib
import struct

import sha
from worker import WorkerBase
from util import uint256_from_str

TEST=0
THRESH=1

def finish_dsha(sha_obj, end):
    sha_obj = sha_obj.copy()
    sha_obj.update(end)
    # return sha.sha256(sha_obj.digest())
    return hashlib.sha256(sha_obj.digest()).digest()

class CpuWorker(WorkerBase):
    def _target(self, difficulty, job_id, extranonce2, ntime, preheader_bin):
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

class FPGAWorker(WorkerBase):
    def __init__(self, cl):
        import fpga
        super(FPGAWorker, self).__init__(cl)

        self.scl = fpga.FPGAController()

    def _target(self, job_id, extranonce2, ntime, preheader_bin):
        try:
            X, Y = sha.precalc(preheader_bin)

            self.scl.start_dsha(X, Y)

            for nonce_bin in self.scl.winning_nonces_gen(X, Y):
                if self._quit:
                    break
                if nonce_bin is None:
                    continue
                nonce = nonce_bin.encode("hex")
                self._cl.submit(job_id, extranonce2, ntime, nonce)

            self._done_ev.set()
        except:
            traceback.print_exc()
            os._exit(1)

