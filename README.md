# Pupil Video Backend

This program helps you to stream the video from another computer or Raspberry pi to your computer where pupil capture software is running. No configuration is needed on the computer where pupil capture software is running. Just Run this program on remote computer with webcam. Make sure pupil capture software is already running before running this program.


Clone the repo
```sh
git clone https://github.com/Lifestohack/pupil-video-backend.git
cd pupil-video-backend
```

# Usage
```sh
from video_backend import *

ip = "127.0.0.1"    # ip address of remote pupil or localhost
port = "50020"      # same as in the pupil remote gui
pupilbackend = VideoBackEnd(ip, port)
pupilbackend.start()
```
If no ip address or port is provided then 127.0.0.1 and 50020 is used respectively by default.

OpenCV is used to get the frames from the camera source. By default camera source 0 is used but the source index can be changed by calling setVideoCaptureParam function. You can also set other parameters like width, height and fps.

If you want to use your own video source instead of built in OpenCV VideoCapture function then see the example at publish_to_pupil.py.
