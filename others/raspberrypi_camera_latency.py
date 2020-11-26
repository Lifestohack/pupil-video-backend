from picamera.array import PiYUVArray
import picamera
from fractions import Fraction
from time import monotonic
import log, logging

resolution = (192, 192)
framerate = 90
time_to_calculate_latency = 5
logging.info(
    "Calculating the Camera lateny. It will take around {} seconds.".format(
        time_to_calculate_latency
    )
)

with picamera.PiCamera() as camera:
    # set camera parameters
    camera.resolution = resolution
    camera.framerate = Fraction(framerate, 1)
    camera.sensor_mode = 7
    rawCapture = PiYUVArray(camera, size=resolution)
    stream = camera.capture_continuous(rawCapture, format="yuv", use_video_port=True)
    latencies = []
    counter = 0
    start_time = monotonic()
    for f in stream:
        frame = f.array
        latency = monotonic() - start_time
        latencies.append(latency)
        rawCapture.truncate(0)
        counter += 1
        if counter >= time_to_calculate_latency * framerate:
            del stream
            break
        start_time = monotonic()

latencies.sort()
latencies = latencies[: int(len(latencies) * 0.99)]
min_lat, avg_lat, max_lat = (
    min(latencies),
    sum(latencies) / len(latencies),
    max(latencies),
)
logging.info(
    "One direction Camera latency calculated between Video backend and Pupil Software."
)
logging.info("Minimum:{} second".format(min_lat))
logging.info("Average:{} second".format(avg_lat))
logging.info("Maximum:{} second".format(max_lat))
