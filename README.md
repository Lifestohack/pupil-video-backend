# Pupil Video Backend
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
