import os
import sys
import time
import socket

import rex

from nxtools import *
from smartcoder import *


def encode(id_asset, id_profile):
    pass


class Worker(object):
    def __init__(self, id_worker):
        self.hostname = socket.gethostname()
        self.id = id_worker
        logging.user = "worker" + str(self.id)
        db = DB()
        db.query("SELECT id FROM nodes WHERE hostname=%s", [self.hostname])
        try:
            self.id_node = db.fetchall()[0][0]
        except IndexError:
            critical_error("This machine is not configured as encoder node")
        db.query("UPDATE jobs SET id_node=NULL, id_worker=NULL, status=0, message='Restarted after worker failure' WHERE id_node=%s AND id_worker=%s", [self.id_node, id_worker])
        self.work()

    def work(self):
        while True:
            try:
                self.main()
            except KeyboardInterrupt:
                print ("")
                logging.warning("Keyboard interrupt. Shutting down worker")
                sys.exit(0)
            except:
                log_traceback()
                critical_error("Unhandled exception in worker. Shutting down")
            time.sleep(5)

    def main(self):
        db = DB()
        job = get_job(self.id_node, self.id, db=db)
        if not job:
            print "no job"
            return
        print "I have job", job.id_asset, job.id_action

if __name__ == "__main__":
    if not sys.argv[-1].isdigit():
        critical_error("Worker accepts only one argument, which must be integer")
    worker = Worker(int(sys.argv[-1]))


