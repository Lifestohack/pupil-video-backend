from time import time
from pupil import PupilManager
import log, logging

host = "10.3.141.136"
port = "50020"

pupil = PupilManager(host, port)

def get_offsets():
    times = []
    for _ in range(60):
        t0 = time()
        t1 = pupil.get_pupil_time()
        t2 = time()
        times.append((t0, t1, t2))
    times.sort(key=lambda t: t[2] - t[0])
    times = times[:int(len(times) * 0.69)]

    # Assuming latency on both direction to be same.
    latency_one_direction = [(t2 - t0) / 2 for t0, _, t2 in times]
    return sum(latency_one_direction) / len(latency_one_direction)
    

latency_one_direction = get_offsets()
logging.info("One direction Network: Calculated between Video backend and Pupil Software: {}second".format(latency_one_direction))
pupil.close()