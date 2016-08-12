#!/usr/bin/env python

import os
import json
import time

from nxtools import *
from pprint import pprint

from transcoder.probe import *

settings = json.load(open("settings.json"))


source_dir = settings["source_dir"]
target_dir = settings["target_dir"]

if __name__ == "__main__":
    for source_path in get_files(source_dir, exts=["mxf"]):
        base_name = get_base_name(source_path)
        target_path = os.path.join(target_dir, "{}.mp4".format(base_name))
        if os.path.exists(target_path):
            continue

        mtime = os.path.getmtime(source_path)
        hrmtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime))
        probe = ffprobe(source_path)
        if probe:
            print probe["format"]["duration"]

        logging.warning("Missing {} ({}) {}".format(target_path, hrmtime, os.path.getsize(source_path)))
