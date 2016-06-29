#!/usr/bin/env python

import json
from transcoder import *

if __name__ == "__main__":
    settings = json.load(open("settings.json"))
    transcoder = Transcoder(**settings)
