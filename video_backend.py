import cv2
from time import monotonic, time
import traceback
from payload import Payload
import threading
from time_sync import Clock_Follower
from pupil import PupilManager
import sys

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
        self.device = device
        self.videosource = videosource
        if videosource is None and callback is None:
            raise ValueError("Please provide callback if you want to use your own video source.")
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
            raise ValueError("Options for devices are: world, eye0, eye1")
        topic = "hmd_streaming." + device
        # Start the plugin
        self.pupil.notify({"subject": plugin_type, "target": device, "name": "HMD_Streaming_Source", "args": {"topics": (topic,)}})
        self._listenAndStartStreaming(self._streamVideo if callback is None else callback)

    def _threadedStream(self, callback):
        thread = threading.Thread(target=callback, args=())
        thread.daemon = True
        self.setVideoCaptureParam(videosource=self.videosource)
        thread.start()

    def _listenAndStartStreaming(self, callback):
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
                self.pupil.close()
        print("Pupil capture software closed.")
        self.initialize()
        self.start(self.device, self.videosource)

    def _streamVideo(self):
        print("Starting the stream for {}".format(self.device))
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
                outstr = "Frames: {}, FPS: {}".format(frame_index, fps) 
                sys.stdout.write('\r'+ outstr)
                counter = counter + 1
                frame_index = frame_index + 1
        except (KeyboardInterrupt, SystemExit):
            print('Exit due to keyboard interrupt')
        except Exception as ex:
            print('Python error with no Exception handler:')
            print('Traceback error:', ex)
            traceback.print_exc()
        finally:
            print("\n" + "Stopping the stream for {}".format(self.device))
            cap.release()

    def setVideoCaptureParam(self, videosource=0, height=240, width=320, frame=30):
        if videosource is None:
            print("Using default camera source: 0")
        self.videosource = 0 if videosource is None else videosource
        self.height = 240 if height is None else height
        self.width = 320 if width is None else width
        self.frame = 30 if frame is None else frame

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
