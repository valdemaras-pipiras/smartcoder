import os
import json
from .common import *


class Manifest():
    def __init__(self, manifest_path):
        logging.debug("Opening manifest {}".format(manifest_path))
        self.manifest_path = manifest_path
        try:
            self.data = json.load(open(self.manifest_path))
        except:
            self.data = {}

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __delitem__(self, key):
        del(self.data[key])

    def save(self):
        f = open(self.manifest_path, "w")
        f.write(json.dumps(self.data))
        f.close()
        if not self.data:
            try:
                os.remove(self.manifest_path)
            except:
                return


class Job():
    def __init__(self, parent, source_path):
        self.parent = parent
        self.source_path = source_path
        self.status = PENDING
        self.last_size = 0
        self.last_size_time = 0
        self._manifest = None
        self.fails = 0
        self.last_fail = 0

    @property
    def manifest(self):
        if not self._manifest:
            self._manifest = Manifest(self.manifest_path)
        return self._manifest

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

    @property
    def manifest_path(self):
        return os.path.join(self.parent.target_dir, "data", "{}.{}".format(self.base_name, "json"))
