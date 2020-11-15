import cv2
from time import monotonic, time, sleep
from payload import Payload
import threading
from time_sync import Clock_Follower
from pupil import PupilManager
import sys
import log
import logging

class VideoBackEnd():
    def __init__(self, host=None, port=None):
        self.host = host
        self.port = port
        self.start_publishing = False
        self.device = "world"
        self.initialize()
    
    def initialize(self):
        self.pupil = PupilManager(self.host, self.port)
        self.msg_streamer = self.pupil.get_msg_streamer()

    def start(self, device="world", videosource=0, callback=None):
        # device = "eye0" or device = "eye1" or device = "world"
        try:
            logging.info("Publishing to device:{}".format(device))
            self.device = device
            self.videosource = videosource
            self.callback = callback
            if self.videosource is None and self.callback is None:
                self.videosource = 0
            if callback is None:
                self.videosource = None
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
            self.pupil.notify({"subject": plugin_type, "target": self.device, "name": "HMD_Streaming_Source", "args": {"topics": (topic,)}})
            self._listenAndStartStreaming(self._streamVideo if self.callback is None else self.callback)
        except Exception as ex:
            logging.error(ex)

    def _threadedStream(self, callback):
        thread = threading.Thread(target=callback, args=())
        thread.daemon = True
        self.setVideoCaptureParam(videosource=self.videosource)
        thread.start()

    def _listenAndStartStreaming(self, callback):
        try:
            if self.device == "world":
                # If videosource is none that means you are implementing your own source. 
                # Call get_pub_socket() to get Message streamer.
                # Call  is_publishable() before publish each payload.
                # Pupil capture software is already notified to start plugin.
                self.start_publishing = True
                self._threadedStream(callback)             
            listen_to_notification = True
            while listen_to_notification:
                message = self.pupil.get_notification()
                if b"eye_process.started" == message[b"subject"] and self.device[-1] == str(message[b"eye_id"]):
                    # If thread has not started then start the thread
                    if self.start_publishing == False:
                        self.start_publishing = True
                        self._threadedStream(callback)
                elif b"eye_process.stopped" == message[b"subject"] and self.device[-1] == str(message[b"eye_id"]):
                    self.start_publishing = False
                elif b"world_process.stopped" == message[b"subject"]:
                    self.start_publishing = False
                    listen_to_notification = False
                    sleep(1)    # sleep here to give time for publishing callback to finish and exit out the callback
                    self.pupil.close()
            logging.info("Pupil capture software closed.")
            self.initialize()
            self.start(self.device, self.videosource, self.callback)
        except Exception as ex:
            logging.error(ex)

    def _streamVideo(self):
        logging.info("Starting the stream for device:{}.".format(self.device))
        frame_index = 1
        fps = 0
        counter = 0
        cap = cv2.VideoCapture(self.videosource)
        cap.set(3, self.width)
        cap.set(4, self.height)
        cap.set(5, self.frame)
        payload = Payload(self.device, self.width, self.height)
        start_time = time()
        try:
            while self.start_publishing == True:
                _, image = cap.read()
                payload.setPayloadParam(time(), image, frame_index)
                self.msg_streamer.send(payload.get())
                seconds = time() - start_time
                if seconds > 1:
                    fps = counter
                    counter = 0
                    start_time = time()
                #outstr = "Frames: {}, FPS: {}".format(frame_index, fps) 
                #sys.stdout.write('\r'+ outstr)
                counter = counter + 1
                frame_index = frame_index + 1
        except (KeyboardInterrupt, SystemExit):
            logging.debug('Exit due to keyboard interrupt')
        except Exception as ex:
            logging.error(ex)
        finally:
            logging.info("Stopping the stream for device: {}.".format(self.device))
            cap.release()
            logging.info("Total Published frames: {}, FPS:{}.".format(frame_index, fps))

    def setVideoCaptureParam(self, videosource=0, height=240, width=320, frame=30):
        self.videosource = 0 if videosource is None else videosource
        self.height = 240 if height is None else height
        self.width = 320 if width is None else width
        self.frame = 30 if frame is None else frame
        logging.info("Using default camera source:{}".format(videosource))
        logging.info("Setting video capture parameters. Height:{}, Width:{}, FPS:{}".format(self.height, self.width, self.frame))

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
