#!/usr/bin/python
from video_backend import VideoBackEnd
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-d','--device', help='Options: world or eye0 or eye1',required=False)
parser.add_argument('-i','--ip',help='Ip address of remote pupil or localhost.', required=False)
parser.add_argument('-p','--port',help='Same as in the pupil remote gui.', required=False)
parser.add_argument('-vs','--videosource',help='Id of the video capturing device to open. Default 0.', required=False)

args = parser.parse_args()


def main(ip, port, device, videosource):
    if ip is None:
        ip = "192.168.0.188"    # ip address of remote pupil or localhost
    if port is None:
        port = "50020"          # same as in the pupil remote gui
    if device is None:
        device = "world"
    if videosource is None:
        videosource = 0
    pupilbackend = VideoBackEnd(ip, port)
    pupilbackend.start("eye0", videosource)

if __name__ == "__main__":
    main(args.ip, args.port, args.device, args.videosource)