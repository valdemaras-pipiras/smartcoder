from __future__ import print_function
from nxtools import *

logging.user = "Transcoder"

PENDING  = 0
WORKING  = 1
FINISHED = 2
ABORTED  = 3
FAILED   = 4
