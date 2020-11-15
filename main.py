#!/usr/bin/python
from video_backend import VideoBackEnd
import argparse
import logging

# set up logging to file - see previous section for more details
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='videobackend.log',
                    filemode='a')
# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# set a format which is simpler for console use
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger().addHandler(console)

parser = argparse.ArgumentParser()
parser.add_argument('-d','--device', help='Options: world or eye0 or eye1',required=False)
parser.add_argument('-i','--ip',help='Ip address of remote pupil or localhost.', required=False)
parser.add_argument('-p','--port',help='Same as in the pupil remote gui.', required=False)
parser.add_argument('-vs','--videosource',help='Id of the video capturing device to open. Default 0.', required=False)
args = parser.parse_args()

def main(ip, port, device, videosource):
    if ip is None:
        ip = "127.0.0.1"    # ip address of remote pupil or localhost
    if port is None:
        port = "50020"          # same as in the pupil remote gui
    if device is None:
        device = "world"
    if videosource is None:
        videosource = 0
    logging.info("Host:{}, Port:{}, Device:{}, Videosource:{}".format(ip, port, device, videosource))
    pupilbackend = VideoBackEnd(ip, port)
    pupilbackend.start(device)

if __name__ == "__main__":
    main(args.ip, args.port, args.device, args.videosource)