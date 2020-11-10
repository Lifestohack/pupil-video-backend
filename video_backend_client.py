from zmq_tools import *
import traceback
import numpy as np
import cv2

addr = '192.168.0.213'  # remote ip or localhost
sub_port = "55555"  # same as in the pupil remote gui
ipc_sub_url = "tcp://{}:{}".format(addr, sub_port)
zmq_ctx = zmq.Context()
sub = Msg_Receiver(zmq_ctx, ipc_sub_url, 
        topics=("hmd_streaming.world",), 
        block_until_connected=True, hwm=2)

try:
    while True:
        topic, msg = sub.recv()
        recent_world = np.frombuffer(msg['__raw_data__'][0], dtype=np.uint8).reshape(msg['height'], msg['width'], 3)
        cv2.imshow(topic, recent_world)
        cv2.waitKey(1)
except Exception as ex:
    print('Python error with no Exception handler:')
    print('Traceback error:', ex)
    traceback.print_exc()