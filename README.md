# Pupil Video Backend

This program helps you to stream the video from another computer or Raspberry pi to your computer where pupil capture software is running. No configuration is needed on the computer where pupil capture software is running. Just Run this program on remote computer with webcam. Make sure pupil capture software is already running before running this program.

Install Dependencies:
```sh
sudo apt install -y python3-opencv
python3 -m pip install pyzmq
python3 -m pip install msgpack==0.5.6

#For the example: raspberrypi.py
sudo apt-get install python3-picamera
```

Clone the repo
```sh
git clone https://github.com/Lifestohack/pupil-video-backend.git
cd pupil-video-backend
```

## Usage
```sh
from video_backend import VideoBackEnd

ip = "127.0.0.1"    # ip address of remote pupil or localhost
port = "50020"      # same as in the pupil remote gui
pupilbackend = VideoBackEnd(ip, port)
pupilbackend.start()  # default is "world". Other options are "eye0" and "eye1".
```
If no ip address or port is provided then 127.0.0.1 and 50020 is used respectively by default.

OpenCV is used to get the frames from the camera source. By default camera source 0 is used but the source index can be changed by calling setVideoCaptureParam function. You can also set other parameters like width, height and fps.

It is listening to the notification published by Pupil capture software. It will not start publishling untill and unless pupil capture software is running. If eye0 or eye1 is requested then make sure to open the window for detecting the eye0 or eye1 is also open.

Run this program three times with different video sources if you want to have world, eye0 and eye1 view on your Pupil capture software.

## Start from terminal
```sh
python main.py [-h] [-d DEVICE] [-i IP] [-p PORT] [-vs VIDEOSOURCE] [-vp VIDEOPARAMETER]
```
Example:
```sh
python main.py -d world -i 127.0.0.1 -p 50020 -vs 0
# -d, -i, -p and -vs are optional. By default world view is streamed using videosource with Id 0.
# -d has three options: world or eye0 or eye1
```

## Callback | Custom Video Source

If you want to use your own video source instead of built in OpenCV VideoCapture function then see the example folder for raspberrpi. It reads the RGB frames from the Raspberry pi camera connected through CSI and publishes it. Basically you need to call the start(callback=yourcustomfunction) function with callback. You can then start sending payload on yourcustomfunction(). if the pupil capture software is running your network. Call is_publishable() to know if you can start publishing the payload or not. is_publishable() will be False when the eye process or world process is stopped. If it started again then the callback will be called again with new Thread. Make sure to exit out of yourcallbackfunction() if is_publishable() is False.

Use get_synced_pupil_time(monotonic()) to get the synced pupil remote time and add it to payload. Do not use your local epoch time but use the local monotonic time and convert it to pupil remote time.
