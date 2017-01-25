from nxtools import *

from .common import *
from .db import *
from .actions import actions
from .assets import *

__all__ = ["Job", "get_job"]

class Job(object):
    def __init__(self, id_asset, id_action, **kwargs):
        self.db = kwargs.get("db", DB())

        self.id_asset = id_asset
        self.id_action = id_action
        self.id_node = None
        self.id_worker = None
        self.status = 0
        self.progress = PENDING
        self.message = "Pending"
        self.creation_time = time.time()
        self.start_time = 0
        self.end_time = 0

        self.asset = Asset(self.id_asset, db=self.db)

        self.db.query("SELECT id_node, id_worker, status, progress, message, creation_time, start_time, end_time FROM jobs WHERE id_asset=%s AND id_action=%s", [self.id_asset, self.id_action])
        result = self.db.fetchall()
        if not result:
            self.is_new = True
            return

        self.is_new = False
        self.id_node, self.id_worker, self.status, self.progress, self.message, self.creation_time, self.start_time, self.end_time = result[0]

    def save(self):
        if self.is_new:
            self.db.query("INSERT INTO jobs VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            [
                self.id_asset,
                self.id_action,
                self.id_node,
                self.id_worker,
                self.status,
                self.progress,
                self.message,
                self.creation_time,
                self.start_time,
                self.end_time
            ])
            self.db.commit()
            self.is_new = False



        else:
            self.db.query(
                "UPDATE jobs SET id_node=%s, id_worker=%s, status=%s, progress=%s, message=%s, creation_time=%s, start_time=%s, end_time=%s WHERE id_asset=%s AND id_action=%s",
                [self.id_node, self.id_worker, self.status, self.progress, self.message, self.creation_time, self.start_time, self.end_time, self.id_asset, self.id_action ]
                )

        jobs = self.asset.report.get("created_jobs", [])
        if not self.id_action in jobs:
            jobs.append(self.id_action)
            self.asset.report["created_jobs"] = jobs
            self.asset.save()


    def update_progress(self, progress=0, message="Job in progress"):
        self.progress = progress
        self.message = message
        if self.is_new:
            return
        self.db.query("UPDATE jobs SET progress=%s, message=%s WHERE id_asset=%s AND id_action=%s", [progress, message])


    def set_finished(self):
        self.status = FINISHED
        self.id_worker = None
        self.id_node = None
        self.save()

    def set_aborted(self):
        self.status = ABORTED
        self.id_worker = None
        self.id_node = None
        self.save()

    def set_failed(self):
        self.status = FAILED
        self.id_worker = None
        self.id_node = None
        self.save()

    def request_abort(self, message="Aborting"):
        self.status = ABORT_REQUIRED
        self.message = message
        self.save()

    def request_restart(self, message="Restart required"):
        self.status = RESTART_REQUIRED
        self.message = message
        self.save()





def get_job(id_node, id_worker, **kwargs):
    db = kwargs.get("db", DB())
    db.query("SELECT id_asset, id_action FROM jobs WHERE status = 0 ORDER BY creation_time DESC")
    for id_asset, id_action in db.fetchall():
        asset = Asset(id_asset, db=db)
        action = actions[id_action]

        print "test", id_asset
        if not action.should_start(asset):
            print "should not start"
            continue

        db.query("""
            UPDATE jobs SET id_node=%s, id_worker=%s, status=1, progress=0, message='Starting', start_time=%s
            WHERE id_asset=%s AND id_action=%s AND id_node IS NULL AND id_worker IS NULL"""
            [id_node, id_worker, time.time(), id_asset, id_action]
            )
        db.commit()
        time.sleep(.2)

        job = Job(id_asset, id_action, db=db)
        if job.id_node != id_node or job.id_worker != id_worker:
            return False

        return job









