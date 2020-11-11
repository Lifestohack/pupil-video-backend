class Payload:

    def __init__(self, topic, width, height, intrinsics=None):
        if intrinsics is None:
            intrinsics = [
                        [0.0, 0.0, 0.0],
                        [0.0, 0.0, 0.0],
                        [0.0, 0.0, 0.0],
                    ]
        if topic is None:
            raise Exception("topic has to be either: world, eye0 or eye1")

        self.payload = {}
        self.payload["format"] = "rgb"
        self.payload["projection_matrix"] = intrinsics
        self.payload["topic"] = "hmd_streaming." + topic
        self.payload["width"] = width
        self.payload["height"] = height

    def setPayloadParam(self, time, frame, index):
        self.payload["timestamp"] = time
        self.payload["__raw_data__"] = [frame]
        self.payload["index"] = index

    def get(self):
        return self.payload
