#!/usr/bin/python
from video_backend import *
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-d','--device', help='Options: world or eye0 or eye1',required=False)
parser.add_argument('-i','--ip',help='Ip address of remote pupil or localhost.', required=False)
parser.add_argument('-p','--port',help='Same as in the pupil remote gui.', required=False)
args = parser.parse_args()


def main(ip, port, device):
    if args.ip is None:
        ip = "192.168.0.188"    # ip address of remote pupil or localhost
    if args.port is None:
        port = "50020"          # same as in the pupil remote gui
    if args.device is None:
        device = "world"
    pupilbackend = VideoBackEnd(ip, port)
    pupilbackend.start(device)

if __name__ == "__main__":
    main(args.ip, args.port, args.device)