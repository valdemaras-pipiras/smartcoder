#!/usr/bin/env python

import sys
import rex

from nxtools import *

from smartcoder import *
from admin import *


if __name__ == "__main__":
    file_monitor = FileMonitor()
    jobs_broker = JobsBroker()

    # And who the fuck watches the watchmen?
    system_monitor = SystemMonitor()
    system_monitor.watch(file_monitor)
    system_monitor.watch(jobs_broker)

    # Admin is blocking. And must not fail :]
    try:
        admin_site_context["system_monitor"] = system_monitor
        admin = CherryAdmin(**admin_config)

    except KeyboardInterrupt:
        print ()
        logging.info("Keyboard interrupt. Shutting down")
        sys.exit(0)

    except Exception:
        log_traceback()
        critical_error("Unhandled exception in Admin module. Exiting.")
        sys.exit(1)
