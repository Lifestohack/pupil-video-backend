from zmq_tools import *
import traceback
addr = '192.168.0.213'  # remote ip or localhost
sub_port = "50020"  # same as in the pupil remote gui
ipc_sub_url = "tcp://{}:{}".format(addr, sub_port)
zmq_ctx = zmq.Context()
sub = Msg_Receiver(zmq_ctx, ipc_sub_url, topics=("hmd_streaming.world",), block_until_connected=True)

try:
    while True:
        topic, msg = sub.recv_topic()
        print(topic)
except Exception as ex:
    print('Python error with no Exception handler:')
    print('Traceback error:', ex)
    traceback.print_exc()