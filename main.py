#!/usr/bin/python
from video_backend import VideoBackEnd
import argparse
import re
import log
import logging
import traceback
import sys

parser = argparse.ArgumentParser()
parser.add_argument(
    "-d", "--device", help="Options: world or eye0 or eye1", required=False
)
parser.add_argument(
    "-i", "--ip", help="Ip address of remote pupil or localhost.", required=False
)
parser.add_argument(
    "-p", "--port", help="Same as in the pupil remote gui.", required=False
)
parser.add_argument(
    "-vs",
    "--videosource",
    help="Id of the video capturing device to open. Default 0.",
    required=False,
)
parser.add_argument(
    "-vp",
    "--videoparameter",
    help='Video parameters. Example: "192, 192, 90". "Height, Width, FPS"',
    required=False,
)
args = parser.parse_args()


def main(host, port, device, videosource, videoparameter):
    height = width = frame = None
    if videoparameter is not None:
        param = videoparameter.split(",")
        height = get_int(param[0])
        width = get_int(param[1])
        frame = get_int(param[2])
    if videosource is not None:
        videosource = get_int(videosource)
    pupilbackend = VideoBackEnd(host, port)
    pupilbackend.setVideoCaptureParam(
        videosource=videosource, height=height, width=width, frame=frame
    )
    pupilbackend.start(device)


def get_int(str):
    try:
        return int(str)
    except Exception:
        logging.error("Format for video parameter -vp are not valid..")
        e = traceback.format_exc()
        logging.error(e)
    sys.exit(0)


if __name__ == "__main__":
    main(args.ip, args.port, args.device, args.videosource, args.videoparameter)
