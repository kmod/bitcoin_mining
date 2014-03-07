import traceback
import os
import time
import struct
import sys

from worker import WorkerBase
from util import uint256_from_str

sys.path.append("/home/kmod/tmp/py-scrypt/build/lib.linux-x86_64-2.7")
import scrypt

TEST = 0

class CpuWorker(WorkerBase):
    def _target(self, difficulty, job_id, extranonce2, ntime, preheader_bin):
        try:
            start = time.time()

            if sys.maxint > 2**32:
                max_nonce = 2**32
            else:
                max_nonce = 2**31 - 1
            i = 0

            THRESH = 0x00010000 / difficulty
            # # THRESH = 1 << difficulty
            # # THRESH /= 4
            # THRESH = 0x00002000
            print "thresh:", THRESH

            hashes_per_thresh = (1 << 32) / THRESH

            if TEST:
                print preheader_bin.encode("hex")
                preheader_bin = "01000000f615f7ce3b4fc6b8f61e8f89aedb1d0852507650533a9e3b10b9bbcc30639f279fcaa86746e1ef52d3edb3c4ad8259920d509bd073605c9bf1d59983752a6b06b817bb4ea78e011d012d59d4".decode("hex")[:-4]

            while i < max_nonce:
                if TEST:
                    i = 0x012d59d4

                if self._quit:
                    print "QUITTING WORKER"
                    break
                if i and i % 10000 == 0:
                    hashrate = i * 1.0 / (time.time() - start + .001)
                    print i, "%.1f kh/s (%.1fs/share))" % (hashrate * 0.001, hashes_per_thresh / hashrate)

                nonce_bin = struct.pack(">I", i)

                header_bin = preheader_bin + nonce_bin
                hash_bin = scrypt.hash(header_bin, header_bin, 1024, 1, 1, 32)

                # print
                # print header_bin.encode("hex")
                # print hash_bin.encode("hex")

                val = struct.unpack("<I", hash_bin[-4:])[0]
                # print val
                # print
                if val < THRESH:
                    nonce = nonce_bin[::-1].encode("hex")
                    print nonce, extranonce2, ntime
                    print hash_bin.encode("hex")
                    hash_int = uint256_from_str(hash_bin)
                    block_hash_hex = "%064x" % hash_int
                    print block_hash_hex


                    self._cl.submit(job_id, extranonce2, ntime, nonce)
                elif val < THRESH*10:
                    print "almost: %d (<%d)" % (val, THRESH)
                i += 1
                # elif i == 0:
                    # print hash_bin.encode("hex")
            self._done_ev.set()
        except:
            traceback.print_exc()
            os._exit(1)

