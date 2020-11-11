import zmq
import cv2
import time
import traceback
import sys
from zmq_tools import *
from payload import *

class VideoBackEnd():
    def __init__(self, ip=None, port=None, hwm=None):

        if ip is None:
            ip = "127.0.0.1"
        if port is None:
            port = "50020"  
        
        icp_req_add = "tcp://{}:{}".format(ip, port)

        # Pupil Software listens to the IPC backend. 
        # The backend is like an echo chamber. 
        # You can either yell something into it, or listen what comes out. 
        # The hmd_streaming plugin listens for what comes out. 
        # You need to yell into it. Request the PUB_PORT from Pupil remote
        # 1. Connect to Pupil Remote
        # 2. Send "PUB_PORT"
        # 3. Receive port number
        # 4. Connect Streamer to pub port

        # Setup zmq context and remote helper
        ctx = zmq.Context()

        # Step 1
        self.pupil_remote = zmq.Socket(ctx, zmq.REQ)
        self.pupil_remote.connect(icp_req_add)

        # Step 2
        self.pupil_remote.send_string("PUB_PORT")
        print("Waiting for the publish port from Pupil Capture software.")

        # Step 3
        pub_port = self.pupil_remote.recv_string()
        print("Publishing to port: {}".format(pub_port))

        # Step 4
        icp_pub_add = "tcp://{}:{}".format(ip, pub_port)
        self.pub_socket = Msg_Streamer(ctx, icp_pub_add, hwm=hwm)


    def start(self, device="world", videosource=0):
        # Start the plugin
        # device = "eye0" or device = "eye1" or device = "world"
        topic = "hmd_streaming." + device
        plugin_type = ""
        if device == "world":
            plugin_type = "start_plugin"
        elif device == "eye0" or device == "eye1":
            plugin_type = "start_eye_plugin"
        else:
            raise ValueError("Options for devices are: world, eye0, eye1")
        notification = self._notify({"subject": plugin_type, "target": device, "name": "HMD_Streaming_Source", "args": {"topics": (topic,)}})
        print("Notification for {}: {}".format(device, notification))
        if videosource is not None:
            self.videosource = videosource
            self.setVideoCaptureParam(videosource=self.videosource)
            self._streamVideo(device)
    
    def get_pub_socket(self):
        return self.pub_socket

    def _notify(self, notification):
        # send notification:
        """Sends ``notification`` to Pupil Remote"""
        topic = "notify." + notification["subject"]
        payload = serializer.dumps(notification, use_bin_type=True)
        self.pupil_remote.send_string(topic, flags=zmq.SNDMORE)
        self.pupil_remote.send(payload)
        return self.pupil_remote.recv_string()

    def setVideoCaptureParam(self, videosource=0, height=240, width=320, frame=30):
        if videosource is None:
            print("Using default camera source: 0")
        self.videosource = 0 if videosource is None else videosource
        self.height = 240 if height is None else height
        self.width = 320 if width is None else width
        self.frame = 30 if frame is None else frame


    def _streamVideo(self, device):
        frame_index = 1
        fps = 0
        counter = 0
        cap = cv2.VideoCapture(self.videosource)
        cap.set(3, self.width)
        cap.set(4, self.height)
        cap.set(5, self.frame)
        payload = Payload(device, self.width, self.height)
        start_time = time.time()
        try:
            while True:
                _, image = cap.read()
                payload.setPayloadParam(time.time(), image, frame_index)
                self.pub_socket.send(payload.get())
                seconds = time.time() - start_time
                if seconds > 1:
                    fps = counter
                    counter = 0
                    start_time = time.time()
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
            cap.release()
            sys.exit(0)