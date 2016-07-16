import os
import sys
import thread
import time
import subprocess

from .common import *
from .job import Job
from .output_format import get_output_format
from .settings import get_settings


class TranscoderWorker():
    def __init__(self, parent):
        self.parent = parent
        self.id = len(self.parent.workers)
        logging.info("Starting {}".format(self))
        self.job = False
        self.last_handle_time = 0

    def __repr__(self):
        return "transcoder worker {}".format(self.id)

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


    def encode_simple(self, output_format, meta):
        logging.info("{} is finalized file (duration: {})".format(self.job, s2tc(meta["duration"])))

        def phandle(position):
            if time.time() - self.last_handle_time < 5:
                return
            position = position / 25.0 #FIXME: get from meta
            progress = (position / meta["duration"]) * 100
            logging.debug("{} encoding {} is at {} ({:.02f}%)".format(self, self.job, s2tc(position),  progress) )
            self.last_handle_time = time.time()

        return ffmpeg(
                self.job.source_path,
                self.job.target_path,
                output_format=output_format,
                progress_handler=phandle
            )


    def encode_growing(self, output_format, meta):
        log_path = os.path.splitext(self.job.target_path)[0] + ".log"
        log_file = open(log_path, "w")

        self.clean_pipe()
        os.mkfifo(self.pipe_path)

        proc = FFMPEG(
                self.pipe_path,
                self.job.target_path,
                output_format=output_format
                )
        proc.start(stderr=log_file)#stderr=subprocess.PIPE)

        source = open(self.job.source_path)
        fifo = open(self.pipe_path, "w")

        buff_size = 1024 * 1024 * 16
        nt = 0
        at = 0
        while True:
            fs = self.job.file_size
            growing = self.job.is_growing

            if (not growing) and at == fs:
                time.sleep(3)
                if self.job.file_size > at:
                    logging.info("quarantine change")
                    continue
                break

            if fs - at < buff_size and growing:
                print("buffer underrun: {} {}".format(fs, at))
                time.sleep(.1)
                continue

            buff = source.read(buff_size)
            fifo.write(buff)
            at += len(buff)

            progress = (float(at)/fs)*100
            if time.time() - nt > 5:
                nt = time.time()
                logging.debug("{} is at byte {} of {} ({:.02f}%)".format(self, at, fs, progress ))

        logging.debug("Size difference: {}".format(self.job.file_size - at))
        logging.debug("Closing {}".format(self.pipe_path))
        log_file.write("------------ TERMINATE ------------\n")
        fifo.close()
        self.clean_pipe()
        t = time.time()
        while proc.is_running:
            logging.debug("Size difference: {}".format(self.job.file_size - at))
            logging.debug(" {} is waiting for ffmpeg termination ({})".format(self, self.job))
            time.sleep(1)
            if time.time() - t > 10:
                logging.warning("{} forcing ffmpeg stop".format(self))
                proc.stop()
        log_file.close()




    def main(self):
        if not os.path.exists(self.job.source_path):
            self.job.status = FAILED
            self.job = False
            return

        start_time = time.time()
        logging.info("{} is encoding {}".format(self, self.job))
        is_growing = self.job.is_growing

        output_format, meta = get_output_format(self.job)
        if not output_format:
            self.job.status = FAILED
            self.job = False
            return

        time.sleep(self.parent.settings["qtime"])

        if self.job.is_growing:
            logging.info("{} is growing file".format(self.job))
            result = self.encode_growing(output_format, meta)
        else:
            logging.info("{} is has source".format(self.job))
            result = self.encode_simple(output_format, meta)

        end_time = time.time()
        elapsed_time = end_time - start_time

        if result:
            speed = meta["duration"] / elapsed_time
            logging.goodnews(
                "Encoding {} finished on {} in {:.02f}s ({:.02f}x real time)".format(
                    self.job,
                    self,
                    elapsed_time,
                    speed
                ))

            self.job.status = FINISHED
        else:
            logging.error(
                "Encoding {} failed after {:02f}s".format(
                    self.job,
                    self.elapsed_time
                ))
            self.job.status = FAILED

        self.job = False



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
                if self.job_exists(source_path):
                    continue
                if self.has_target(source_path):
                    continue
                self.jobs.append(Job(self, source_path))
                new_job_count += 1

            if new_job_count:
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
        return False


    def has_target(self, source_path):
        base_name =  get_base_name(source_path)
        for ext in ["mp4", "txt"]:
            f =  os.path.join(self.target_dir, "{}.{}".format(base_name, ext))
            if os.path.exists(f):
                return True
        return False
