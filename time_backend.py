from time import time, sleep, monotonic

class TimeManager():

    def __init__(self, pupil_remote):
        self.pupil_remote = pupil_remote
        self.offset = self.get_offset()

    def get_pupil_time(self):
        self.pupil_remote.send_string('t')
        return self.pupil_remote.recv_string()

    def get_offset(self):
        times = []
        for _ in range(100):
            t0 = monotonic()
            t1 = self.get_pupil_time()
            t2 = monotonic() 
            times.append((t0, t1, t2))
        offsets = [t0 - ((float(t1) + (t2 - t0) / 2)) for t0, t1, t2 in times]
        mean_offset = sum(offsets) / len(offsets)
        offset_jitter = sum([abs(mean_offset - o) for o in offsets]) / len(offsets)
        return mean_offset, offset_jitter

    def time(self):
        """
        return time after sync
        """
        raise NotImplementedError()