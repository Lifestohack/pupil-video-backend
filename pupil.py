import zmq
from time import monotonic
from zmq_tools import Msg_Streamer
import msgpack as serializer
import logging


class PupilManager:
    def __init__(self, host=None, port=None, hwm=None):
        self.host = host
        self.port = port
        self.hwm = hwm
        if self.host is None:
            self.host = "127.0.0.1"
        if self.port is None:
            self.port = "50020"
        logging.info("Host:{}, Port:{}".format(self.host, self.port))
        self.initialize()

    def initialize(self):
        """
        Pupil Software listens to the IPC backend.
        The backend is like an echo chamber.
        You can either yell something into it, or listen what comes out.
        The hmd_streaming plugin listens for what comes out.
        You need to yell into it. Request the PUB_PORT from Pupil remote
        1. Connect to Pupil Remote
        2. Send "PUB_PORT"
        3. Receive port number
        4. Connect Streamer to pub port
        """

        # Setup zmq context and remote helper
        ctx = zmq.Context()

        # Step 1
        self.pupil_remote = zmq.Socket(ctx, zmq.REQ)
        icp_req_add = "tcp://{}:{}".format(self.host, self.port)
        self.pupil_remote.connect(icp_req_add)

        # Step 2, 3
        logging.info("Waiting for Pupil remote.")
        pub_port = self._get_port("PUB_PORT")
        icp_pub_add = "tcp://{}:{}".format(self.host, pub_port)

        # Step 4
        self.msg_streamer = Msg_Streamer(ctx, icp_pub_add, hwm=self.hwm)

        # Setting up sub port to subscribe to notification
        sub_port = self._get_port("SUB_PORT")
        self.subscriber = ctx.socket(zmq.SUB)
        icp_sub_add = "tcp://{}:{}".format(self.host, sub_port)
        self.subscriber.connect(icp_sub_add)
        self.subscriber.subscribe("notify.")
        logging.info("Connection Successful.")

    def _get_port(self, type):
        self.pupil_remote.send_string(type)
        logging.debug("Waiting for the {} from Pupil Capture software.".format(type))
        port = self.pupil_remote.recv_string()
        logging.debug("{}: {}".format(type, port))
        return port

    def get_msg_streamer(self):
        return self.msg_streamer

    def get_notification(self):
        _, payload = self.subscriber.recv_multipart()
        message = serializer.loads(payload)
        logging.debug(message)
        return message

    def get_pupil_remote(self):
        return self.pupil_remote

    def get_pupil_time(self):
        self.pupil_remote.send_string("t")
        return self.pupil_remote.recv_string()

    def notify(self, notification):
        # send notification:
        """Sends ``notification`` to Pupil Remote"""
        topic = "notify." + notification["subject"]
        payload = serializer.dumps(notification, use_bin_type=True)
        self.pupil_remote.send_string(topic, flags=zmq.SNDMORE)
        self.pupil_remote.send(payload)
        return self.pupil_remote.recv_string()

    def close(self):
        self.pupil_remote.close()
        self.subscriber.close()
