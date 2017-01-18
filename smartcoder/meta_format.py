from nxtools import *

meta_format = {
        "duration" : s2time,
        "aspect_ratio" : lambda x: "1:{:.02f}".format(x),
        "ctime" : format_time,
        "mtime" : format_time
    }
