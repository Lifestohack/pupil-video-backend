from time import time, sleep, monotonic

class Clock_Follower():
    """
    Clock follower
    
    https://github.com/pupil-labs/pupil/blob/master/pupil_src/shared_modules/time_sync_spec.md

    The clock follower calculates its clock's offset and offset-jitter regularly in the following manner:

    Open a TCP connection to the time service.
    Repeat the following steps 60 times:
        Measure the follower's current timestamp t0
        Send sync to the clock master
        Receive the clock master's response as t1 and convert it into a float
        Measure the follower's current timestamp as t2
        Store entry t0, t1, t2
    Sort entries by roundtrip time (t2 - t0) in ascending order
    Remove last 30% entries, i.e. remove outliers
    Calculate offset for each entry: t0 - (t1 + (t2 - t0) / 2)
    Calculate mean offset
    Calculate offset variance
    Use mean offset as offset and clock variance as offset jitter
    Adjust the follower's clock according to the offset and the offset jitter
    
    """

    def __init__(self, pupil_remote):
        self.pupil_remote = pupil_remote
        mean_offset, offset_jitter = self.get_offsets()
        self.offset = mean_offset + offset_jitter

    def get_pupil_time(self):
        self.pupil_remote.send_string('t')
        return self.pupil_remote.recv_string()

    def get_offsets(self):
        times = []
        for _ in range(60):
            t0 = monotonic()
            t1 = self.get_pupil_time()
            t2 = monotonic() 
            times.append((t0, t1, t2))
        times.sort(key=lambda t: t[2]-t[0])
        times = times[:int(len(times)*0.69)]
        # assuming latency on both direction to be same
        offsets = [t0 - ((float(t1) + (t2 - t0) / 2)) for t0, t1, t2 in times]
        mean_offset = sum(offsets) / len(offsets)
        offset_jitter = sum([abs(mean_offset - o) for o in offsets]) / len(offsets)
        return mean_offset, offset_jitter

    def get_synced_pupil_time(self, localtime):
        """
        Returns time after sync.
        localtime is monotonic as offset was calculated using monotonic.
        """
        return localtime + self.offset