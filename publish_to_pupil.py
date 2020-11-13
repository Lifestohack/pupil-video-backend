from video_backend import VideoBackEnd
from picamera import PiCamera
from picamera.array import PiRGBArray
from picamera.array import PiYUVArray
import numpy as np
import threading
import sys
from payload import Payload
import time, traceback

# Helper class implementing an IO deamon thread
class StartThreadToStream:

    def __init__(self, pub_socket):
        self.newpayload = False
        self.payload = None
        self.pub_socket = pub_socket
        self._stop = False
        self._thread = threading.Thread(target=self._run, args=())
        self._thread.daemon = True
        self._thread.start()
    
    def _run(self):
        while not self._stop:
            if self.newpayload == True:
                self.newpayload = False
                #f = self.payload[0][:,:,0]      # If only brightness information is needed from yuv format and not rgb 
                self.pub_socket.send(self.payload)
            else:
                time.sleep(0.0001)

    def dataready(self, payload):
        self.payload = payload
        self.newpayload = True

    def close(self):
        self._stop = True


ip = "127.0.0.1"    # ip address of remote pupil or localhost
port = "50020"      # same as in the pupil remote gui
device = "world"
backend = VideoBackEnd(ip, port)

def streamVideo():
    resolution =  (320, 240)
    framerate = 90
    pub_socket = backend.get_pub_socket()
    # initialize the stream
    camera = PiCamera()
    time.sleep(2.0)  # Warmup time; needed by PiCamera on some RPi's
    # set camera parameters
    camera.resolution = resolution
    camera.framerate = framerate
    # Pupils capture software rotates HMD Streaming Source 180 degree.
    # Sending rotated video so it shows correctly
    camera.rotation = 180    
    rawCapture = PiRGBArray(camera, size=resolution)
    #rawCapture = PiYUVArray(camera, size=resolution)
    stream = camera.capture_continuous(rawCapture,
        format="rgb", use_video_port=True)
    frame_counter_per_sec = 0
    frame_index = 1
    start_time = time.time()
    #streamimage = StartThreadToStream(pub_socket)
    payload = Payload(device, resolution[0], resolution[1])
    fps = 0
    try:
        for f in stream:
            if backend.is_publishable():
                # grab the frame from the stream and clear the stream in
                # preparation for the next frame
                frame = f.array
                payload.setPayloadParam(time.time(), frame, frame_index)
                #streamimage.dataready(payload.get())    #   give it to StartThreadToStream to publish
                pub_socket.send(payload.get())         #   publish here
                seconds = time.time() - start_time
                if seconds > 1:
                    fps = frame_counter_per_sec
                    frame_counter_per_sec = 0
                    start_time = time.time()
                outstr = "Frames: {}, FPS: {}".format(frame_index, fps) 
                sys.stdout.write('\r'+ outstr)
                frame_counter_per_sec = frame_counter_per_sec + 1
                frame_index = frame_index + 1
                rawCapture.truncate(0)
            else:
                break
    except (KeyboardInterrupt, SystemExit):
        print('Exit due to keyboard interrupt')
    except Exception as ex:
        print('Python error with no Exception handler:')
        print('Traceback error:', ex)
        traceback.print_exc()
    finally:
        #streamimage.close()
        camera.close()

def main():
    backend.start(device, callback=streamVideo)

if __name__ == "__main__":
    main()
