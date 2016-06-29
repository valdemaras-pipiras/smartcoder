from __future__ import print_function

import os
import sys
import thread

from .common import *

class Job():
    def __init__(self, parent, source_path):
        self.parent = parent
        self.source_path = source_path
        self.status = PENDING

    def __repr__(self):
        return "job {}".format(self.base_name)

    @property
    def base_name(self):
        return get_base_name(self.source_path)

    @property
    def target_path(self):
        return os.path.join(self.parent.target_dir, "{}.{}".format(self.base_name, self.parent.settings["container"]))


class TranscoderThread():
    def __init__(self, parent):
        self.parent = parent
        self.id = len(self.parent.threads)
        logging.info("Starting {}".format(self))
        self.job = False

    @property
    def is_busy(self):
        return bool(self.job)

    def start_job(self, job):
        self.job = job
        self.job.status = WORKING
        thread.start_new_thread(self.main, ())

    def __repr__(self):
        return "transcoder thread {}".format(self.id)

    def main(self):
        if not self.job:
            return
        elif os.path.exists(self.job.target_path):
            logging.debug("Target path for {} already exists. Aborting job".format(self.job.base_name))
            self.job.status = ABORTED
            return


class Transcoder():
    def __init__(self, **kwargs):
        self.source_dir = kwargs.get("source_dir", "input")
        self.target_dir = kwargs.get("target_dir", "output")
        self.num_threads = kwargs.get("num_threads", 4)
        self.settings = {
                "container" : kwargs.get("container", "mp4"),
                "video_bitrate" : kwargs.get("video_bitrate"),
                "loop_delay" : int(kwargs.get("loop_delay", 5)),
                "source_exts" : kwargs.get("source_exts", [])
            }

        self.jobs = []
        self.threads = []
        for i in range(self.num_threads):
            self.threads.append(TranscoderThread(self))
        self.work()


    def work(self):
        while True:
            try:
                self.main()
                time.sleep(self.settings["loop_delay"])
            except KeyboardInterrupt:
                print ()
                logging.warning("Shutting down")
                break

        sys.exit(0) #TODO: Graceful exit



    def job_exists(self, source_path):
        for job in self.jobs:
            if job.source_path == source_path:
                return True
        return False

    @property
    def free_threads(self):
        for thread in self.threads:
            if thread.is_busy:
                continue
            yield thread

    def get_next_job(self):
        for job in self.jobs:
            if job.status == PENDING:
                return job
        return False


    def main(self):
        """
        1) get new job
        2) assign to free thread
        3) ???
        4) profit
        """
        new_job_count = 0
        for source_path in get_files(self.source_dir, exts=self.settings["source_exts"]):
            if self.job_exists(source_path):
                continue
            self.jobs.append(Job(self, source_path))
            new_job_count += 1

        if new_job_count:
            logging.info("Created {} new jobs".format(new_job_count))

        for thread in self.free_threads:
            job = self.get_next_job()
            if not job:
                logging.warning("No new job")
            else:
                logging.info("Assigning {} to {}".format(job, thread))
                thread.start_job(job)









