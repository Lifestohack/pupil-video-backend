from picamera.array import PiYUVArray
import picamera
from fractions import Fraction
from time import monotonic
import logging, log
import cv2

resolution = (192, 192)
framerate = 90
time_to_calculate_latency = 5
logging.info(
    "Calculating the Camera lateny. It will take around {} seconds.".format(
        time_to_calculate_latency
    )
)

cap = cv2.VideoCapture(0)
cap.set(3, resolution[1])
cap.set(4, resolution[0])
cap.set(5, framerate)
ret, frame = cap.read()
if not ret:
    logging.critical("Can't receive frame (stream end?). Exiting ...")
    exit(0)
hertz = cap.get(5)
width = frame.shape[1]
height = frame.shape[0]
if width != resolution[1] or height != resolution[0] or framerate != hertz:
    logging.info(
        "Camera changed capture parameters. Height:{}, Width:{}, FPS:{}".format(
            height, width, hertz
        )
    )
latencies = []
counter = 0
start_time = monotonic()
for _ in range(int(hertz * time_to_calculate_latency)):
    _, image = cap.read()
    latency = monotonic() - start_time
    latencies.append(latency)
    counter += 1
    start_time = monotonic()
cap.release()
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
