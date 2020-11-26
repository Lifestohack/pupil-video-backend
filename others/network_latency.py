from time import time, sleep
from pupil import PupilManager
import log, logging


def get_network_latency():
    host = "10.3.141.136"
    port = "50020"
    pupil = PupilManager(host, port)
    times = []
    logging.info("Calculating the network lateny...")
    for _ in range(100):
        sleep(0.003)  # simulate spaced requests as in real world
        t0 = time()
        pupil.get_pupil_time()
        t1 = time()
        times.append((t0, t1))
    # Assuming latency on both direction to be same.
    latency_one_direction = [(t1 - t0) / 2 for t0, t1 in times]
    pupil.close()
    return (
        min(latency_one_direction),
        sum(latency_one_direction) / len(latency_one_direction),
        max(latency_one_direction),
    )


if __name__ == "__main__":
    min_lat, avg_lat, max_lat = get_network_latency()
    logging.info(
        "One direction Network latency calculated between Video backend and Pupil Software."
    )
    logging.info("Minimum:{} second".format(min_lat))
    logging.info("Average:{} second".format(avg_lat))
    logging.info("Maximum:{} second".format(max_lat))
