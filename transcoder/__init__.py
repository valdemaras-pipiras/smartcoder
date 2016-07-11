import os
import sys
import thread

from .common import *
from .job import Job
from .output_format import get_output_format
from .settings import get_settings


class TranscoderThread():
    def __init__(self, parent):
        self.parent = parent
        self.id = len(self.parent.threads)
        logging.info("Starting {}".format(self))
        self.job = False

    def __repr__(self):
        return "transcoder thread {}".format(self.id)

    def __del__(self):
        self.clean_pipe()

    @property
    def is_busy(self):
        return bool(self.job)

    @property
    def pipe_path(self):
        return "fifo_{}.mxf".format(self.id) #TODO: abs path to temp??

    def clean_pipe(self):
        if os.path.exists(self.pipe_path):
            os.remove(self.pipe_path)

    def start_job(self, job):
        self.job = job
        self.job.status = WORKING
        if not self.job:
            return
        elif os.path.exists(self.job.target_path):
            logging.debug("Target path for {} already exists. Aborting.".format(self.job.base_name))
            self.job.status = ABORTED
            self.job = False
            return
        thread.start_new_thread(self.main, ())

    def main(self):
        output_format = get_output_format(self.job)
        #TODO: error handling

        #print (" ".join([str(item) for sublist in output_format for item in sublist]))
        #print ("\n")
        #self.job.status = FINISHED
        #self.job = False
        #return

        self.clean_pipe()
        os.mkfifo(self.pipe_path)

        proc = FFMPEG(
                self.pipe_path,
                self.job.target_path,
                output_format=output_format
                )
        proc.start(stderr=None)

        source = open(self.job.source_path)
        fifo = open(self.pipe_path, "w")

        while self.job.is_growing:
            try:
                fifo.write(source.read())
                time.sleep(.1)
            except:
                log_traceback()
                self.job.status = FAILED
                self.job = False
                fifo.close()
                self.clean_pipe()
                return

        self.job.status = FINISHED
        self.job = False
        fifo.close()
        self.clean_pipe()



class Transcoder():
    def __init__(self, **kwargs):
        self.source_dir = kwargs.get("source_dir", "input")
        self.target_dir = kwargs.get("target_dir", "output")
        self.settings = get_settings(**kwargs)

        self.jobs = []
        self.threads = []
        for i in range(self.settings["threads"]):
            self.threads.append(TranscoderThread(self))

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
                if self.job_exists(source_path):
                    continue
                #TODO: skip if target path exists
                logging.debug("Found new file {}".format(os.path.basename(source_path)))
                self.jobs.append(Job(self, source_path))
                new_job_count += 1

            if new_job_count:
                logging.info("Created {} new jobs".format(new_job_count))

            time.sleep(self.settings["loop_delay"])


    def broker(self):
        logging.info("Starting jobs broker")
        while True:
            time.sleep(.5)

            thread = self.get_free_thread()
            if not thread:
                continue

            job = self.get_next_job()
            if not job:
                continue

            logging.info("Assigning {} to {}".format(job, thread))
            thread.start_job(job)

    #
    # Helpers
    #

    def job_exists(self, source_path):
        for job in self.jobs:
            if job.source_path == source_path:
                return True
        return False

    def get_free_thread(self):
        for thread in self.threads:
            if thread.is_busy:
                continue
            return thread
        return False

    def get_next_job(self):
        for job in self.jobs:
            if job.status == PENDING:
                return job
        return False
