import os
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
