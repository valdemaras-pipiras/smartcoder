import time
import thread

from nxtools import *

from .common import *
from .db import *
from .assets import *
from .actions import *

__all__ = ["JobsBroker"]


class JobsBroker(object):
    def __init__(self):
        self.broker_cache = {}
        thread.start_new_thread(self.work, ())

    def is_working(self):
        return time.time() - self.last_seen < 1800

    def work(self):
        while True:
            self.last_seen = time.time()
            self.main()
            time.sleep(5)

    def main(self):
        actions = []
        db = DB()
        db.query("SELECT id, title, settings FROM actions")
        for id, title, settings in db.fetchall():
            actions.append(Action(id, title, settings, db=db))

        if not actions:
            return

        for asset in get_assets(db=db):
            created_actions = self.broker_cache.get(asset.id, [])

            for id_action in actions:
                if action.id in created_actions:
                    continue

#            if job exists
#                self.broker_cache
