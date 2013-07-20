class RecentCache(object):
    """
    very simple LRU-ish cache
    """
    def __init__(self, n):
        self.d1 = {}
        self.d2 = {}
        self._n = n

    def __setitem__(self, k, v):
        print k, v
        self.d1[k] = v
        self.d2.pop(k, None)
        if len(self.d1) >= self._n:
            self.d2 = self.d1
            self.d1 = {}

    def __getitem__(self, k):
        if k in self.d1:
            return self.d1[k]
        return self.d2[k]
