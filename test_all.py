#!/usr/bin/env python

import os
import json

from nxtools import *
from pprint import pprint

from transcoder.probe import *

settings = json.load(open("settings.json"))

class Manifest():
    def __init__(self, source_path):
        self.base_name = get_base_name(source_path)
        self.manifest_path = os.path.join(settings["target_dir"], "data", "{}.{}".format(base_name, "json"))
        try:
            self.data = json.load(open(self.manifest_path))
        except:
            self.data = {}

    def get(self, key, default):
        return self.data.get(key, default)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def save(self):
        f = open(self.manifest_path, "w")
        f.write(json.dumps(self.data))



TEST_VERSION = 1



for source_path in get_files("/mnt/RK13/clip.dir", exts=["mxf"]):
    base_name = get_base_name(source_path)
    manifest = Manifest(source_path)

    if manifest.get("re-encode", False):
        continue

    if manifest.get("status", "") == "ok" and manifest.get("test_version", 0) >= TEST_VERSION:
        continue


    logging.debug("Testing {}".format(source_path))
    meta = probe(source_path)

    if not meta:
        logging.debug("Skipping corrupted file {}".format(base_name))
        continue

    if manifest.get("timecode", "00:00:00:00") !=  meta["timecode"]:
        logging.info("{} will be re-encoded (timecode burn-in)".format(base_name))
        manifest = Manifest(source_path)
        manifest["re-encode"] = True
        manifest["reason"] = "Timecode Burn-In"
        manifest.save()
        continue

    target_path = os.path.join(settings["target_dir"], "{}.mp4".format(base_name))
    target_meta = probe(target_path)
    if not target_meta:
        logging.info("{} will be re-encoded (corrupted file)".format(base_name))
        manifest["re-encode"] = True
        manifest["reason"] = "Corrupted file"
        manifest.save()
        continue

    sdur = meta["duration"]
    tdur = target_meta["duration"]

    if sdur > tdur + 1:
        diff = "{:.02f}".format(sdur - tdur)
        logging.info("{} will be re-encoded (duration mismatch: {})".format(base_name, diff))
        manifest = Manifest(source_path)
        manifest["re-encode"] = True
        manifest["reason"] = "Duration mismatch"
        manifest.save()
        continue


    manifest = Manifest(source_path)
    manifest["status"] = "ok"
    manifest["test_version"] = TEST_VERSION
    manifest.save()
