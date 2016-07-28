#!/usr/bin/env python

import json

from transcoder import *
from optparse import OptionParser

if __name__ == "__main__":

    settings = json.load(open("settings.json"))

    parser = OptionParser()
    parser.add_option("-f", "--fix", action="store_true", dest="is_fixing", help="Fix only")
    parser.add_option("-w", "--workers", action="append", default=4, type="int", dest="workers", help="Workers count")

    options, args = parser.parse_args()
    option_dict = vars(options)

    settings.update(option_dict)
    transcoder = Transcoder(**settings)
