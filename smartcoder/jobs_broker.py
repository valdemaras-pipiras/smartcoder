import time
import thread

from nxtools import *

from .common import *
from .db import *
from .assets import *
from .actions import actions
from .jobs import Job

__all__ = ["JobsBroker"]

class JobsBroker(object):
    def __init__(self):
        thread.start_new_thread(self.work, ())

    def is_working(self):
        return time.time() - self.last_seen < 1800

    def work(self):
        if not actions:
            logging.warning("No action defined. Stopping JobsBroker")
            return
        while True:
            self.last_seen = time.time()
            self.main()
            time.sleep(5)

    def main(self):
        db = DB()
        for asset in get_assets(db=db):
            for id_action in actions:
                action = actions[id_action]
                if not action.should_allow(asset):
                    continue

                if action.should_create(asset):
                    if asset.has_job(action.id):
                        continue

                    logging.info("JobsBroker: Creating job {} for {}".format(asset, action))
                    job = Job(asset.id, action.id, db=db)
                    job.save()

