import os
import sys
import thread
import time
import json

from .common import *
from .job import Job
from .settings import get_settings
from .worker import TranscoderWorker


class Transcoder():
    def __init__(self, **kwargs):
        self.source_dir = kwargs.get("source_dir", "input")
        self.target_dir = kwargs.get("target_dir", "output")
        self.settings = get_settings(**kwargs)
        self.jobs = []
        self.workers = []
        for i in range(self.settings["workers"]):
            self.workers.append(TranscoderWorker(self))

        thread.start_new_thread(self.watch, ())
        self.broker()

    #
    # Main loops
    #

    def watch(self):
        """watchfolder thread"""
        logging.info("Watching folder {}".format(self.source_dir))
        while True:
            new_job_count = 0
            for source_path in get_files(self.source_dir, exts=self.settings["source_exts"]):

                if not (os.path.exists(source_path) and os.path.getsize(source_path)):
                    continue # Na soubory s nulovou delkou sere pes

                if self.job_exists(source_path):
                    continue

                if self.has_target(source_path):
                    continue

                self.jobs.append(Job(self, source_path))
                new_job_count += 1

            if new_job_count:
                if new_job_count == 1:
                    logging.info("Last created job: {}".format(source_path))
                logging.info("Created {} new jobs".format(new_job_count))

            time.sleep(self.settings["loop_delay"])


    def broker(self):
        logging.info("Starting jobs broker")
        while True:
            time.sleep(.5)

            worker = self.get_free_worker()
            if not worker:
                continue

            job = self.get_next_job()
            if not job:
                continue

            logging.info("Assigning {} to {}".format(job, worker))
            worker.start_job(job)

    #
    # Helpers
    #

    def job_exists(self, source_path):
        for job in self.jobs:
            if job.source_path == source_path:
                return True
        return False


    def get_free_worker(self):
        for worker in self.workers:
            if worker.is_busy:
                continue
            return worker
        return False


    def get_next_job(self):
        for job in self.jobs:
            if job.status == PENDING:
                return job
            elif job.status == FAILED and job.fails < 5 and time.time() - job.last_fail > 60:
                return job
            elif job.status == FAILED and time.time() - job.last_fail > 3600:
                # jednou za hodinu se pokusime projet zfailovany joby
                return job
        return False


    def has_target(self, source_path):
        base_name =  get_base_name(source_path)
        if self.settings["is_fixing"]:

            manifest_name = os.path.join(self.target_dir, "data", "{}.{}".format(base_name, "json"))
            try:
                manifest = json.load(open(manifest_name))
            except:
                pass
            else:
                if manifest.get("re-encode", False):
                    logging.info("Restarting job {} ({})".format(base_name, manifest.get("reason", "no reason")))
                    return False
            return True

        else:
            for ext in ["mp4", "txt", "json"]:
                f =  os.path.join(self.target_dir, "{}.{}".format(base_name, ext))
                if os.path.exists(f):
                    return True
            return False
