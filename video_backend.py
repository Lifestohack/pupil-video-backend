import msgpack as serializer
import zmq
import cv2
import time
import sys
import traceback
from zmq_tools import *

addr = '127.0.0.1'  # remote ip or localhost
pub_port = "50020"  # same as in the pupil remote gui
ipc_pub_url = "tcp://{}:{}".format(addr, pub_port)
zmq_ctx = zmq.Context()
pupil_socket = Msg_Streamer(zmq_ctx, ipc_pub_url)

width = 320
height = 240
frame = 90
intrinsics = [
                [406.74054872359386, 0.0, 332.0196776862145],
                [0.0, 392.27339466867005, 242.29314229816816],
                [0.0, 0.0, 1.0],
            ]
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
cap.set(cv2.CAP_PROP_FPS, frame)

index = 1

try:
  print("Opened!!!")
  while True:
    payload = {}
    ret, image = cap.read()
    payload["timestamp"] = time.time()
    payload["__raw_data__"] = [image]
    payload["topic"] = "hmd_streaming.world"
    payload["width"] = width
    payload["height"] = height
    payload["index"] = index
    payload["format"] = "rgb"
    payload["projection_matrix"] = intrinsics
    index = index + 1
    pupil_socket.send(payload)
    print(index)
except (KeyboardInterrupt, SystemExit):
    print('Exit due to keyboard interrupt')
except Exception as ex:
    print('Python error with no Exception handler:')
    print('Traceback error:', ex)
    traceback.print_exc()
finally:
  cap.release()
  sys.exit(0)




