from time import monotonic


class Clock_Follower:

    # https://github.com/pupil-labs/pupil/blob/master/pupil_src/shared_modules/time_sync_spec.md

    def __init__(self, pupil_remote, time):
        self.time = time
        self.pupil_remote = pupil_remote
        mean_offset, offset_jitter = self.get_offsets()
        self.offset = mean_offset + offset_jitter

    def get_offsets(self):
        times = []
        for _ in range(60):
            t0 = self.time()
            t1 = self.pupil_remote.get_pupil_time()
            t2 = self.time()
            times.append((t0, t1, t2))
        times.sort(key=lambda t: t[2] - t[0])
        times = times[: int(len(times) * 0.69)]

        # Assuming latency on both direction to be same.
        offsets = [t0 - ((float(t1) + (t2 - t0) / 2)) for t0, t1, t2 in times]
        mean_offset = sum(offsets) / len(offsets)

        # Jitter is the deviation from the clock's ideal behavior.
        # It means the clock edges weren't where you expected them to.
        offset_jitter = sum([abs(mean_offset - o) for o in offsets]) / len(offsets)
        return mean_offset, offset_jitter

    def get_synced_pupil_time(self, localtime):
        """
        Returns time after sync.
        """
        return (
            localtime - self.offset
            if localtime > self.offset
            else localtime + self.offset
        )
