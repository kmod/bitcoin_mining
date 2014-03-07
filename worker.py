import threading

class WorkerBase(object):
    def __init__(self, cl):
        self._cl = cl
        self._quit = True

        self._done_ev = threading.Event()
        self._done_ev.set()

    def start(self, job_id, extranonce2, ntime, preheader_bin):
        self._quit = False
        self._done_ev.clear()
        t = threading.Thread(target=self._target, args=(job_id, extranonce2, ntime, preheader_bin))
        t.setDaemon(True)
        t.start()

    def stop(self):
        self._quit = True
        self._done_ev.wait()

