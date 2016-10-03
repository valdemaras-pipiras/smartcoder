import os
import sys
import thread
import time
import subprocess
import json

from .common import *
from .job import Job
from .output_format import get_output_format


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
        thread.start_new_thread(self.main, ())

    def job_fail(self):
        self.job.status = FAILED
        self.job.fails += 1
        self.job.last_fail = time.time()
        self.job = False

    #
    # Main proc
    #

    def main(self):
        if not os.path.exists(self.job.source_path):
            self.job_fail()
            return

        start_time = time.time()
        logging.info("{} is encoding {}".format(self, self.job))
        is_growing = self.job.is_growing

        output_format, meta = get_output_format(self.job)
        if not output_format:
            self.job_fail()
            return

        time.sleep(self.parent.settings["qtime"])

        with open("current_{}".format(self.id), "w") as f:
            f.write(self.job.base_name)

        try:
            #if self.job.is_growing:
            if not self.parent.settings["is_fixing"]:
                logging.debug("{} is growing file".format(self.job))
                result = self.encode_growing(output_format, meta)
            else:
                logging.debug("Fixing {}".format(self.job))
                result = self.encode_simple(output_format, meta)
        except:
            log_traceback()
            result = False

        end_time = time.time()
        elapsed_time = end_time - start_time
        if "re-encode" in self.job.manifest.data.keys():
            del(self.job.manifest["re-encode"])
            del(self.job.manifest["reason"])
            self.job.manifest.save()

        if meta["timecode"] != "00:00:00:00":
            self.job.manifest["timecode"] = meta["timecode"]
            self.job.manifest.save()

            tc_path = os.path.splitext(self.job.target_path)[0] + ".xml"
            with open(tc_path, "w") as f:
                f.write("<IN>{}</IN>".format(meta["timecode"]))

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
                    elapsed_time
                ))
            self.job_fail()

        self.job = False

        with open("current_{}".format(self.id), "w") as f:
            f.write("None")

    #
    # Encoding variants
    #

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
        proc.start(stderr=log_file)

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
                    logging.info("{} changed in quarantine limit".format(self.job.base_name))
                    continue
                break

            if fs - at < buff_size and growing:
                time.sleep(1)
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
        return True
