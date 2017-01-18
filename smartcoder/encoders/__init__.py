from .ffmpeg import *
from .themis import *
from .aura import *

__all__ = ["sc_encoders"]

sc_encoders = {
        "ffmpeg" : SCffmpeg,
        "themis" : SCthemis,
        "aura" : SCaura
    }
