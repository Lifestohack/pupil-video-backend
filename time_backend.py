from time import time, sleep

class TimeManager():

    def __init__(self, pupil_remote):
        self.latency = None
        self.pupil_time = None
        self.synced_time = None
        self.pupil_remote = pupil_remote

    
    def get_pupil_time(self):
        self.pupil_remote.send_string('t')
        self.pupil_time = self.pupil_remote.recv_string()
        return self.pupil_time

    def get_latency(self):
        latencys = []
        for _ in range(100):
            t0 = time()
            t1 = self.get_pupil_time()
            t2 = time()
            latency = (t2 - t0) / 2     # one-way latency. Same latency is assumed both ways
            latencys.append(latency)
        return min(latencys), max(latencys), sum(latencys)/len(latencys)

    def sync_time(self):
        """
        time sync with pupil capture host
        """

        # set value for self.synced_time after sync
        raise NotImplementedError()

    def time(self):
        """
        return time after sync
        """
        return self.synced_time