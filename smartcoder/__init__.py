from .common import *
from .db import *
from .assets import *
from .actions import *
from .jobs import *

from .file_monitor import *
from .system_monitor import *
from .jobs_broker import *


def load_config():
    db = DB()
    db.query("SELECT id, mountpoint FROM storages")
    for id, mountpoint in db.fetchall():
        storages[id] = mountpoint

    db.query("SELECT id, title, settings FROM actions")
    for id, title, settings in db.fetchall():
        logging.info("Initialising action: {}".format(title))
        actions[id] = Action(id, title, settings)

load_config()
