from video_backend import VideoBackEnd

ip = "192.168.0.188"    # ip address of remote pupil or localhost
port = "50020"      # same as in the pupil remote gui
pupilbackend = VideoBackEnd(ip, port)
pupilbackend.start()  # default is "world". Other options are "eye0" and "eye1".