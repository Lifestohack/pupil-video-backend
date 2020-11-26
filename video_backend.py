import cv2
from time import monotonic, time, sleep
from payload import Payload
import threading
from time_sync import Clock_Follower
from pupil import PupilManager
import sys
import log
import logging
import os, traceback


class VideoBackEnd:
    def __init__(self, host=None, port=None):
        self.host = host
        self.port = port
        self.start_publishing = False
        self.device = "world"
        self.initialize()
        self.videosource = 0
        self.height = 192
        self.width = 192
        self.frame = 90

    def initialize(self):
        self.pupil = PupilManager(self.host, self.port, hwm=1)
        self.msg_streamer = self.pupil.get_msg_streamer()
        self.clock = Clock_Follower(self.pupil, monotonic)

    def start(self, device="world", callback=None):
        # device = "eye0" or device = "eye1" or device = "world"
        try:
            self.device = device
            self.callback = callback
            if self.device is None:
                self.device = "world"
            plugin_type = ""
            if self.device == "world":
                plugin_type = "start_plugin"
            elif self.device == "eye0" or self.device == "eye1":
                plugin_type = "start_eye_plugin"
            else:
                err = "Options for devices are: world, eye0, eye1"
                logging.critical(err)
                raise ValueError(err)
            topic = "hmd_streaming." + self.device
            # Start the plugin
            notification = {
                "subject": plugin_type,
                "target": self.device,
                "name": "HMD_Streaming_Source",
                "args": {"topics": (topic,), "hwm": 1},
            }
            logging.debug(notification)
            self.pupil.notify(notification)
            self._listenAndStartStreaming(
                self._streamVideo if self.callback is None else self.callback
            )
        except Exception:
            exp = traceback.format_exc()
            logging.error(exp)

    def _threadedStream(self, callback):
        thread = threading.Thread(target=callback, args=())
        thread.daemon = True
        thread.start()
        return thread

    def _listenAndStartStreaming(self, callback):
        logging.info("Will publish to device:{}".format(self.device))
        thread = None
        try:
            if self.device == "world":
                # If videosource is none that means you are implementing your own source.
                # Call get_pub_socket() to get Message streamer.
                # Call  is_publishable() before publish each payload.
                # Pupil capture software is already notified to start plugin.
                self.start_publishing = True
                thread = self._threadedStream(callback)
            listen_to_notification = True
            while listen_to_notification:
                message = self.pupil.get_notification()
                if b"eye_process.started" == message[b"subject"] and self.device[
                    -1
                ] == str(message[b"eye_id"]):
                    # If thread has not started then start the thread
                    if self.start_publishing == False:
                        self.start_publishing = True
                        thread = self._threadedStream(callback)
                elif b"eye_process.stopped" == message[b"subject"] and self.device[
                    -1
                ] == str(message[b"eye_id"]):
                    self.start_publishing = False
                    if thread is not None:
                        thread.join()
                elif b"world_process.stopped" == message[b"subject"]:
                    self.start_publishing = False
                    listen_to_notification = False
        except (KeyboardInterrupt, SystemExit):
            logging.info("Exit due to keyboard interrupt")
            self.start_publishing = False
            if thread is not None:
                thread.join()
            self.close()
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)
        except Exception:
            exp = traceback.format_exc()
            logging.error(exp)
        finally:
            if thread is not None:
                thread.join()
            self.close()
            logging.info("Pupil capture software closed.")
        # Re-Initialize again and start listening to pupil remote
        self.initialize()
        self.start(self.device, self.callback)

    def _streamVideo(self):
        try:
            logging.info("Using default camera source:{}".format(self.videosource))
            logging.info(
                "Setting video capture parameters. Height:{}, Width:{}, FPS:{}".format(
                    self.height, self.width, self.frame
                )
            )
            logging.info("Starting the stream for device:{}.".format(self.device))
            frame_index = 1
            fps = 0
            counter = 1
            cap = cv2.VideoCapture(self.videosource)
            if not cap.isOpened():
                logging.critical(
                    "Cannot open camera for camera index {}".format(self.videosource)
                )
                exit(0)
            cap.set(3, self.width)
            cap.set(4, self.height)
            cap.set(5, self.frame)
            ret, frame = cap.read()
            if not ret:
                logging.critical("Can't receive frame (stream end?). Exiting ...")
                exit(0)
            hertz = cap.get(5)
            width = frame.shape[1]
            height = frame.shape[0]
            payload = Payload("world", width, height)
            if self.width != width or self.height != height or self.frame != hertz:
                logging.info(
                    "Camera changed capture parameters. Height:{}, Width:{}, FPS:{}".format(
                        height, width, hertz
                    )
                )
            self.height = height
            self.width = width
            self.frame = hertz
            payload = Payload(self.device, self.width, self.height)
            start_time = time()
            image_read_time = time()
            while self.start_publishing == True:
                _, image = cap.read()
                latency = time() - image_read_time
                payload.setPayloadParam(
                    self.get_synced_pupil_time(monotonic()), image, frame_index
                )
                self.msg_streamer.send(payload.get())
                seconds = time() - start_time
                if seconds > 1:
                    fps = counter
                    counter = 0
                    start_time = time()
                outstr = "Frames: {}, FPS: {}, Frame Read latency: {}".format(
                    frame_index, fps, latency
                )
                sys.stdout.write("\r" + outstr)
                counter = counter + 1
                frame_index = frame_index + 1
                image_read_time = time()
        except (KeyboardInterrupt, SystemExit):
            logging.info("Exit due to keyboard or SystemExit interrupt")
        except Exception:
            exp = traceback.format_exc()
            logging.error(exp)
        finally:
            logging.info("Stopping the stream for device: {}.".format(self.device))
            cap.release()
            logging.info("Total Published frames: {}, FPS:{}.".format(frame_index, fps))

    def setVideoCaptureParam(self, videosource=0, height=192, width=192, frame=90):
        self.videosource = 0 if videosource is None else videosource
        self.height = 192 if height is None else height
        self.width = 192 if width is None else width
        self.frame = 90 if frame is None else frame

    def get_msg_streamer(self):
        """
        Returns Msg_Streamer
        Usages:
            get_msg_streamer().send(payload)
        See payload.py for payload format.
        """
        return self.msg_streamer

    def is_publishable(self):
        # loop over is_publishable to publish each payload.
        # It is needed because if eye process or world process is stopped then it doesnot make sense to stream video
        return self.start_publishing

    def get_synced_pupil_time(self, localtime):
        return self.clock.get_synced_pupil_time(localtime)

    def close(self):
        if self.pupil is not None:
            self.pupil.close()
