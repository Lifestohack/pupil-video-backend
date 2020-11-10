from zmq_tools import *

addr = '192.168.0.213'  # remote ip or localhost
req_port = "50020"  # same as in the pupil remote gui
ipc_sub_url = "tcp://{}:{}".format(addr, req_port)
zmq_ctx = zmq.Context()
notify_sub = Msg_Receiver(zmq_ctx, ipc_sub_url, topics=("hmd_streaming.world",), block_until_connected=True)

try:
    while True:
        topic, msg = notify_sub.recv_topic()
        print(topic)
except Exception:
    pass
