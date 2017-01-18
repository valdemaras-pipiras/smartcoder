from .common import *
from .db import *
from .assets import *

from .file_monitor import *
from .system_monitor import *
from .jobs_broker import *


def load_config():
    db = DB()
    db.query("SELECT id, mountpoint FROM storages")
    for id, mountpoint in db.fetchall():
        storages[id] = mountpoint


load_config()
