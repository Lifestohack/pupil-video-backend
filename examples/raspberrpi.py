from video_backend import VideoBackEnd
import picamera
from picamera.array import PiRGBArray
from picamera.array import PiYUVArray
import numpy as np
import threading
import sys
from payload import Payload
import traceback
from time import sleep, time, monotonic
import log
import logging
import numpy
import cv2
from fractions import Fraction

""" 
    This example is just meant to send the Y part of YUV for the eye0 process. 
    Send one channel gray frame to pupil capture software.
"""

ip = "10.3.141.136"  # ip address of remote pupil or localhost
port = "50020"  # same as in the pupil remote gui
device = "eye0"

# initialize the stream
backend = VideoBackEnd(ip, port)

# Helper class implementing an IO deamon thread
class StartThreadToStream:
    """
    Using new thread to send the the frame
    """

    def __init__(self, pub_socket, device, resolution, backend):
        self.backend = backend
        self.newpayload = False
        self.frame = None
        self.frame_index = 1
        self.monotonic = 0
        self.pub_socket = pub_socket
        self._stop = False
        self._thread = threading.Thread(target=self._run, args=())
        self._thread.daemon = True
        self._thread.start()
        self.payload = Payload(device, resolution[0], resolution[1], "gray")

    def _run(self):
        while not self._stop:
            if self.newpayload == True:
                self.newpayload = False
                frame = numpy.ascontiguousarray(self.frame)
                self.payload.setPayloadParam(
                    self.backend.get_synced_pupil_time(self.monotonic),
                    frame,
                    self.frame_index,
                )
                self.pub_socket.send(self.payload.get())
            else:
                sleep(0.001)

    def dataready(self, frame, frame_index, time_monotonic):
        self.frame = frame
        self.frame_index = frame_index
        self.monotonic = time_monotonic
        self.newpayload = True

    def close(self):
        self._stop = True


def streamVideo():
    resolution = (192, 192)
    fps = 90
    pub_socket = backend.get_msg_streamer()
    # Make sure to set up raspberry pi camera
    # More information here: https://www.raspberrypi.org/documentation/configuration/camera.md
    with picamera.PiCamera() as camera:
        # set camera parameters
        camera.resolution = resolution
        camera.framerate = Fraction(fps, 1)
        # camera.sensor_mode = 7
        # camera.exposure_mode = 'off'
        # camera.shutter_speed = 6000000
        # camera.iso = 1600
        # rawCapture = PiRGBArray(camera, size=resolution)
        rawCapture = PiYUVArray(camera, size=resolution)
        stream = camera.capture_continuous(
            rawCapture, format="yuv", use_video_port=True
        )
        frame_counter_per_sec = 0
        frame_index = 1
        streamimage = StartThreadToStream(pub_socket, device, resolution, backend)
        # payload = Payload(device, resolution[0], resolution[1], "gray")    # use this if sending without new thread StartThreadToStream
        fps = 0
        start_time = time()
        image_read_time = time()
        try:
            for f in stream:
                if backend.is_publishable():
                    # grab the frame from the stream and clear the stream in
                    # preparation for the next frame
                    frame = f.array
                    capture_time = monotonic()
                    latency = time() - image_read_time
                    streamimage.dataready(
                        frame[:, :, 0], frame_index, capture_time
                    )  #   give it to StartThreadToStream to publish
                    """ 
                    # use this also if sending without new thread StartThreadToStream but deactivate above line
                    payload.setPayloadParam(capture_time, numpy.ascontiguousarray(frame[:,:,0]), frame_index)
                    pub_socket.send(payload.get())           #   publish here
                    """
                    seconds = time() - start_time
                    if seconds > 1:
                        fps = frame_counter_per_sec
                        frame_counter_per_sec = 0
                        start_time = time()
                    outstr = "Frames: {}, FPS: {}, Frame Read latency: {}".format(
                        frame_index, fps, latency
                    )
                    sys.stdout.write("\r" + outstr)
                    frame_counter_per_sec = frame_counter_per_sec + 1
                    frame_index = frame_index + 1
                    rawCapture.truncate(0)
                    image_read_time = time()
                else:
                    break
        except (KeyboardInterrupt, SystemExit):
            logging.info("Exit due to keyboard interrupt")
        except Exception:
            exp = traceback.format_exc()
            logging.error(exp)
        finally:
            streamimage.close()
            del stream
            del streamimage
            del rawCapture
            logging.info("Total Published frames: {}, FPS:{}.".format(frame_index, fps))
            logging.info("Streaming stopped for the device: {}.".format(device))


if __name__ == "__main__":
    backend.start(device, callback=streamVideo)
