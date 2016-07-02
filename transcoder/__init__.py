import os
import sys
import thread

from .common import *
from .job import Job
from .output_format import get_output_format


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
        output_format = get_output_format(self.job)
        #TODO: error handling

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
        self.thread_count = kwargs.get("thread_count", 1)
        self.settings = {
                # Frame settings

                "frame_rate" : kwargs.get("frame_rate", 25),
                "pixel_format" : kwargs.get("pixel_format", "yuv420p"),
                "width" : kwargs.get("width", 720),
                "height" : kwargs.get("height", 576),
                "logo" : kwargs.get("logo", False),

                # Video encoder settings

                "container" : kwargs.get("container", "3g2"),
                "video_codec" : kwargs.get("video_codec", "libx264"),
                "video_bitrate" : kwargs.get("video_bitrate", "2000k"),
                "x264_profile" : kwargs.get("x264_profile", "main"),
                "x264_preset" : kwargs.get("x264_preset", "medium"),
                "x264_level" : kwargs.get("x264_level", "4.0"),

                # Audio encoder settings

                "audio_codec" : kwargs.get("audio_codec", "libfdk_aac"),
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
