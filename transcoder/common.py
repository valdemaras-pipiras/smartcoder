from __future__ import print_function

import time

from nxtools import *

DEBUG     = 0
INFO      = 1
WARNING   = 2
ERROR     = 3
GOOD_NEWS = 4

log_format = {
    DEBUG     : "{}  DEBUG      {}\n",
    INFO      : "{}  INFO       {}\n",
    WARNING   : "{}  WARNING    {}\n",
    ERROR     : "{}  ERROR      {}\n",
    GOOD_NEWS : "{}  GOOD NEWS  {}\n"
    }


def log_handler(**kwargs):
    date = time.strftime("%Y-%m-%d")
    with (open("log/{}.log".format(date),"a")) as f:
        msg = log_format[kwargs["message_type"]].format(
		time.strftime("%Y-%m-%d %H:%M:%S"),
		kwargs["message"]
	    )
        f.write(msg)


logging.user = "Transcoder"
logging.add_handler(log_handler)

PENDING  = 0
WORKING  = 1
FINISHED = 2
ABORTED  = 3
FAILED   = 4
