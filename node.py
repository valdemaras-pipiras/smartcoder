#!/usr/bin/env python

import os
import sys
import time
import subprocess


class WorkerWrapper(object):
    def __init__(self, parent, id):
        self.parent = parent
        self.id = id


class Node():
    def __init__(self):
        self.workers = []

    def spawn_worker(self, id):
        self.workers.append(WorkerWrapper(self, id))


if __name__ == "__main__":
    node = Node()
