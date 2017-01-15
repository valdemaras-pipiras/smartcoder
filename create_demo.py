#!/usr/bin/env python


# [title, mountpoint]

STORAGES = [
        ["demo", "/mnt/share/Work/demodata/"]
    ]

# [id_storage, relative path, config]
#
# config accepts following keys:
# - recursive (bool, default False)
# - extensions (list, default ["mxf"])
#

WATCHFOLDERS = [
        [1, "smartcoder/clip.dir", {}]
    ]

ACTIONS = [
        ["proxy", "support/proxy.xml"]
    ]

# [hostname, worker_count]
NODES = [
        ["banana", 3]
    ]

# [login, password (plain), is_admin]
USERS = [
        ["demo", "demo", True]
    ]




#
# Install everything
#

import rex
import json

from smartcoder.db import DB
from smartcoder.common import hash_password

def truncate(db):
    db.query("""TRUNCATE TABLE
            storages,
            watchfolders,
            assets,
            actions,
            nodes,
            jobs,
            users
            RESTART IDENTITY
        """)
    db.commit()

if __name__ == "__main__":
    db = DB()
    truncate(db)

    for storage_data in STORAGES:
        db.query("INSERT INTO storages (title, mountpoint) VALUES (%s, %s)", storage_data)

    for id_storage, path, config in WATCHFOLDERS:
        db.query("INSERT INTO watchfolders (id_storage, path, settings) VALUES (%s, %s, %s)", [id_storage, path, json.dumps(config)])

    for title, settings_path in ACTIONS:
        settings = open(settings_path).read()
        db.query("INSERT INTO actions (title, settings) VALUES (%s, %s)", [title, settings])

    for hostname, workers_count in NODES:
        db.query("INSERT INTO nodes (hostname, workers_count) VALUES (%s, %s)", [hostname, workers_count])

    for login, password, is_admin in USERS:
        db.query("INSERT INTO users (login, password, is_admin) VALUES (%s, %s, %s)", [login, hash_password(password), is_admin])

    db.commit()
