import zmq
import cv2
import time
import traceback
import sys
from zmq_tools import Msg_Streamer
from payload import Payload
import msgpack as serializer
import threading

class VideoBackEnd():
    def __init__(self, ip=None, port=None, hwm=None):
        self.ip = ip
        self.port = port
        self.hwm = hwm
        if self.ip is None:
            self.ip = "127.0.0.1"
        if self.port is None:
            self.port = "50020"  
        self.start_publishing = False
        self.device = "world"
        self._initialize()
        
    def _initialize(self):
        icp_req_add = "tcp://{}:{}".format(self.ip, self.port)
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
        print("Waiting for the PUB_PORT from Pupil Capture software.")

        # Step 3
        pub_port = self.pupil_remote.recv_string()
        print("Publishing to port: {}".format(pub_port))

        # Step 4
        icp_pub_add = "tcp://{}:{}".format(self.ip, pub_port)
        self.pub_socket = Msg_Streamer(ctx, icp_pub_add, hwm=self.hwm)

        # subscribe to notification
        self.pupil_remote.send_string("SUB_PORT")
        sub_port = self.pupil_remote.recv_string()
        print("Waiting for the SUB_PORT from Pupil Capture software.")
        self.subscriber = ctx.socket(zmq.SUB)
        self.subscriber.connect(f'tcp://{self.ip}:{sub_port}')
        self.subscriber.subscribe('notify.')  # receive all gaze messages
        print("Listening to port: {}".format(sub_port))

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
            _, payload = self.subscriber.recv_multipart()
            message = serializer.loads(payload)
            print(message)
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
        print("Pupil capture software closed.")
        self._initialize()
        self.start(self.device, self.videosource)

    def _threadedStream(self, callback):
        thread = threading.Thread(target=callback, args=())
        thread.daemon = True
        self.setVideoCaptureParam(videosource=self.videosource)
        thread.start()

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
        self._notify({"subject": plugin_type, "target": device, "name": "HMD_Streaming_Source", "args": {"topics": (topic,)}})
        self._listenAndStartStreaming(self._streamVideo if callback is None else callback)

    def get_pub_socket(self):
        # returns Msg_Streamer
        # call get_pun_socket(payload)
        return self.pub_socket

    def is_publishable(self):
        # loop over is_publishable to publish each payload.
        # It is needed because if eye process or world process is stopped then it doesnot make sense to stream video
        return self.start_publishing

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
        start_time = time.time()
        try:
            while self.start_publishing == True:
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
            print("\n" + "Stopping the stream for {}".format(self.device))
            cap.release()
            sys.exit(0)