import zmq
import cv2
import time
import traceback
import sys
from zmq_tools import *

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

        # Step 3
        pub_port = self.pupil_remote.recv_string()
        print("Publishing to port: {}".format(pub_port))

        # Step 4
        icp_pub_add = "tcp://{}:{}".format(ip, pub_port)
        self.pub_socket = Msg_Streamer(ctx, icp_pub_add, hwm=hwm)
        self.setVideoCaptureParam()


    def start(self, world=True, eye0=False, eye1=False):
        # Start the plugin
        if world == True:
            world_notification = self._notify({"subject": "start_plugin", "name": "HMD_Streaming_Source", "args": {"topics": ("hmd_streaming.world",)}})
            print("World View notification:", world_notification)
            self._streamVideo()
        if eye0 == True:
            self._notify({"subject": "start_eye_plugin", "name": "HMD_Streaming_Source", "args": {"topics": ("hmd_streaming.eye0",)}})
            print("World View notification:", world_notification)
        if eye1 == True:
            self._notify({"subject": "start_eye_plugin", "name": "HMD_Streaming_Source", "args": {"topics": ("hmd_streaming.eye1",)}})
            print("World View notification:", world_notification)


    def _notify(self, notification):
        # send notification:
        """Sends ``notification`` to Pupil Remote"""
        topic = "notify." + notification["subject"]
        payload = serializer.dumps(notification, use_bin_type=True)
        self.pupil_remote.send_string(topic, flags=zmq.SNDMORE)
        self.pupil_remote.send(payload)
        return self.pupil_remote.recv_string()

    def setVideoCaptureParam(self, source=0, height=240, width=320, frame=30):
        if source is None:
            print("Using default camera source: 0")
        self.source = 0 if source is None else source
        self.height = 240 if height is None else height
        self.width = 320 if width is None else width
        self.frame = 30 if frame is None else frame


    def _streamVideo(self):
        intrinsics = [
                        [0.0, 0.0, 0.0],
                        [0.0, 0.0, 0.0],
                        [0.0, 0.0, 0.0],
                    ]
        index = 1
        fps = 0
        counter = 0
        cap = cv2.VideoCapture(0)
        cap.set(3, self.width)
        cap.set(4, self.height)
        cap.set(5, self.frame)
        start_time = time.time()
        try:
            while True:
                payload = {}
                _, image = cap.read()
                height, width, _ = image.shape
                payload["timestamp"] = time.time()
                payload["__raw_data__"] = [image]
                payload["topic"] = "hmd_streaming.world"
                payload["width"] = width
                payload["height"] = height
                payload["index"] = index
                payload["format"] = "rgb"
                payload["projection_matrix"] = intrinsics
                self.pub_socket.send(payload)
                seconds = time.time() - start_time
                if seconds > 1:
                    fps = counter
                    counter = 0
                    start_time = time.time()
                outstr = "Frames: {}, FPS: {}".format(index, fps) 
                sys.stdout.write('\r'+ outstr)
                counter = counter + 1
                index = index + 1
        except (KeyboardInterrupt, SystemExit):
            print('Exit due to keyboard interrupt')
        except Exception as ex:
            print('Python error with no Exception handler:')
            print('Traceback error:', ex)
            traceback.print_exc()
        finally:
            cap.release()
            sys.exit(0)