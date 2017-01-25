import os
import thread
from nxtools import *

from .common import *
from .db import *
from .assets import *


__all__ = ["FileMonitor"]


class SCWatchFolder(WatchFolder):
    def process(self, input_path):
        db = self["db"]
        id_storage = self["id_storage"]
        asset_path = os.path.join(self.input_dir, input_path)
        full_path = os.path.join(get_path(id_storage, asset_path))
        base_name = get_base_name(asset_path)

        ctime = os.path.getctime(full_path)
        mtime = os.path.getmtime(full_path)
        fsize = self.process_file_size

        if self["quarantine_time"] and time.time() - mtime < self["quarantine_time"]:
            logging.debug("{} is too young. Skipping".format(base_name))

        asset = asset_by_path(id_storage, asset_path, db=db)
        is_new = False

        if not asset:
            is_new = True
            asset = Asset(db=db)
            asset.id_storage = id_storage
            asset.path = asset_path
            try:
                asset.save()
            except IntegrityError:
                logging.warning(path, "is already registered asset. This should never happen")
                db.commit()
            except Exception:
                log_traceback()
                return
            logging.info("Created new {}".format(asset))

        if asset.ctime != ctime or asset.mtime != mtime:
            logging.info("Updating asset {}".format(asset.id))
            asset.ctime = ctime
            asset.mtime = mtime
            asset.report["created_jobs"] = []
            asset.probe()
            asset.save()

            if not is_new:
                db.query("UPDATE jobs SET status = %s WHERE id_asset = %s", [RESTART_REQUIRED, asset.id])
                db.commit()




class FileMonitor(object):
    def __init__(self):
        self.last_seen = time.time()
        self.watchfolders = []
        self.db = DB()
        self.db.query("SELECT id_storage, path, settings FROM watchfolders")
        for id_storage, path, settings in self.db.fetchall():
            watchfolder_path = get_path(id_storage, path)
            self.watchfolders.append(SCWatchFolder(
                        watchfolder_path,
                        relative_path=True,

                        db=self.db,
                        id_storage=id_storage,
                        quarantine_time=settings.get("quarantine_time", 0),

                        recursive=settings.get("recursive", False),
                        hidden=settings.get("hidden", False),
                        case_sensitive_exts=settings.get("case_sensitive_exts", False)
                    ))

        thread.start_new_thread(self.work, ())

    def is_working(self):
        return time.time() - self.last_seen < 1800

    def work(self):
        last_clean_up = time.time()
        while True:
            self.last_seen = time.time()
            for watchfolder in self.watchfolders:
                watchfolder.watch()

            if time.time() - last_clean_up > 1800:
                for watchfolder in self.watchfolders:
                    watchfolder.clean_up()
                last_clean_up = time.time()

            time.sleep(5)
