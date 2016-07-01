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
        self.last_size = 0
        self.last_size_time = 0

    @property
    def file_size(self):
        f = open(self.source_path)
        f.seek(0, 2)
        return f.tell()

    @property
    def is_growing(self):
        file_size = self.file_size
        if self.last_size == self.last_size_time == 0 or self.last_size != self.file_size:
            self.last_size_time = time.time()
            self.last_size = file_size
            return True
        elif time.time() - self.last_size_time > self.parent.settings["qtime"]:
            logging.info("{} is not growing anymore".format(self.base_name))
            return False
        else:
            return True # jsme v ochranne dobe, pocitame, ze furt roste

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
        if not self.job:
            return
        elif os.path.exists(self.job.target_path):
            logging.debug("Target path for {} already exists. Aborting job".format(self.job.base_name))
            self.job.status = ABORTED
            self.job = False
            return
        thread.start_new_thread(self.main, ())

    def __repr__(self):
        return "transcoder thread {}".format(self.id)

    @property
    def pipe_path(self):
        return "fifo_{}.mxf".format(self.id) #TODO: abs path to temp??

    def clean_pipe(self):
        if os.path.exists(self.pipe_path):
            os.remove(self.pipe_path)


    def main(self):
        meta = ffprobe(self.job.source_path)
        duration = meta["format"].get("duration",0)
        logging.debug("source duration is {}".format(duration))

        self.clean_pipe()
        os.mkfifo(self.pipe_path)

        proc = FFMPEG(
                self.pipe_path,
                self.job.target_path,
                output_format=self.parent.output_format
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
        self.thread_count = kwargs.get("thread_count", 1)
        self.settings = {
                # Frame settings

                "frame_rate" : kwargs.get("frame_rate", 25),
                "pixel_format" : kwargs.get("pixel_format", "yuv420p"),
                "width" : kwargs.get("width", 1024),
                "height" : kwargs.get("height", 576),
                "logo" : kwargs.get("logo", False),

                # Video encoder settings

                "container" : kwargs.get("container", "mpeg"),
                "video_bitrate" : kwargs.get("video_bitrate", "2000k"),
                "x264_profile" : kwargs.get("x264_profile", "main"),
                "x264_preset" : kwargs.get("x264_preset", "medium"),
                "x264_level" : kwargs.get("x264_level", "4.0"),

                # Audio encoder settings

                "audio_bitrate" : kwargs.get("audio_bitrate", "128k"),
                "audio_sample_rate" : kwargs.get("audio_sample_rate", 48000),

                # Daemon settings

                "qtime" : int(kwargs.get("qtime", 10)),
                "loop_delay" : int(kwargs.get("loop_delay", 5)),
                "source_exts" : kwargs.get("source_exts", ["mxf"])
                }

        self.jobs = []
        self.threads = []
        for i in range(self.thread_count):
            self.threads.append(TranscoderThread(self))
        self.work()


    @property
    def output_format(self):
        filter_array = []
        if self.settings.get("logo", False):
            filter_array.append(
                    "movie={}[watermark];[watermark]scale={}:{}[watermark]".format(
                        self.settings["logo"],
                        self.settings["width"],
                        self.settings["height"]
                        )
                    )
        filter_array.append("[in]null[out]")
        if self.settings.get("expand_levels"):
            filter_array.append("[out]colorlevels=rimin=0.0625:gimin=0.0625:bimin=0.0625:rimax=0.9375:gimax=0.9375:bimax=0.9375[out]")
        filter_array.append("[out]scale={}:{}[out]".format(self.settings["width"], self.settings["height"]))
        if self.settings.get("logo", False):
            filter_array.append("[out][watermark]overlay=0:0[out]")
        filters = ";".join(filter_array)
        return [
                ["filter:v", filters],
                ["r", self.settings["frame_rate"]],
                ["pix_fmt", self.settings["pixel_format"]],

                ["c:v", "libx264"],
                ["b:v", self.settings["video_bitrate"]],
                ["profile:v" , self.settings["x264_profile"]],
                ["level", self.settings["x264_level"]],
                ["preset:v", self.settings["x264_preset"]],
                ["video_track_timescale", self.settings["frame_rate"]],

                ["c:a", "libfdk_aac"],
                ["b:a", self.settings["audio_bitrate"]],
                ["ar", self.settings["audio_sample_rate"]],
            ]


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
        threads = []
        for thread in self.threads:
            if thread.is_busy:
                continue
            threads.append(thread)
        return threads


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
            break

        if new_job_count:
            logging.info("Created {} new jobs".format(new_job_count))

        while self.free_threads:
            job = self.get_next_job()
            if not job:
                break
            thread = self.free_threads[0]
            logging.info("Assigning {} to {}".format(job, thread))
            thread.start_job(job)









