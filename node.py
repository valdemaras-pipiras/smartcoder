#!/usr/bin/env python

import os
import sys
import time
import subprocess
import socket

import rex

from nxtools import *
from smartcoder import *


class WorkerWrapper(object):
    def __init__(self, parent, id):
        self.parent = parent
        self.id = id
        self.proc = None

    def main(self, **kwargs):
        if not self.proc:
            self.spawn()
            return

        if self.proc.poll() != None:
            logging.warning("Worker {} terminated. Restarting".format(self.id))
            self.spawn()
            return

    def spawn(self):
        cmd = ["python", "worker.py", str(self.id)]
        self.proc = subprocess.Popen(cmd)


class Node(object):
    def __init__(self):
        self.hostname = socket.gethostname()

        db = DB()
        db.query("SELECT id, workers_count FROM nodes WHERE hostname=%s", [self.hostname])
        result = db.fetchall()
        if not result:
            critical_error("This machine is not configured as encoder node")
        self.id, self.workers_count = result[0]
        self.workers = []
        for i in range(self.workers_count):
            self.workers.append(WorkerWrapper(self, i))
        self.work()

    def work(self):
        while True:
            self.main()
            time.sleep(5)

    def main(self):
        for worker in self.workers:
            worker.main()



if __name__ == "__main__":
    node = Node()
