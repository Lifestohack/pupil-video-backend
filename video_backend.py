import zmq
import cv2
import time
import sys
import traceback
from zmq_tools import *

# Setup zmq context and remote helper
ctx = zmq.Context()

pupil_remote = zmq.Socket(ctx, zmq.REQ)
pupil_remote.connect("tcp://127.0.0.1:50020")
pupil_remote.send_string("PUB_PORT")
pub_port = pupil_remote.recv_string()

icp_pub_add = "tcp://127.0.0.1:{}".format(pub_port)
pub_socket = Msg_Streamer(ctx, icp_pub_add, hwm=2)

# send notification:
def notify(notification):
    """Sends ``notification`` to Pupil Remote"""
    topic = "notify." + notification["subject"]
    payload = serializer.dumps(notification, use_bin_type=True)
    pupil_remote.send_string(topic, flags=zmq.SNDMORE)
    pupil_remote.send(payload)
    return pupil_remote.recv_string()

# Start the annotations plugin
notify({"subject": "start_plugin", "name": "HMD_Streaming_Source", "args": {"topics": ("hmd_streaming.world",)}})

intrinsics = [
                [406.74054872359386, 0.0, 332.0196776862145],
                [0.0, 392.27339466867005, 242.29314229816816],
                [0.0, 0.0, 1.0],
            ]
height = 360
width = 640
frame = 90
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
cap.set(cv2.CAP_PROP_FPS, frame)
index = 1
# World: Attempt to load unknown plugin: hmd_streaming
try:
  while True:
    payload = {}
    ret, image = cap.read()
    payload["timestamp"] = time.time()
    payload["__raw_data__"] = [image]
    payload["topic"] = "hmd_streaming.world"
    payload["width"] = width
    payload["height"] = height
    payload["index"] = index
    payload["format"] = "bgr"
    payload["projection_matrix"] = intrinsics
    pub_socket.send(payload)
    print(index)
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