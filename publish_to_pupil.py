from video_backend import *

ip = "127.0.0.1"    # ip address of remote pupil or localhost
port = "50020"      # same as in the pupil remote gui
backend = VideoBackEnd(ip, port)
backend.start()