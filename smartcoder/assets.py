import json

from nxtools import *

from .common import *
from .db import *
from .probe import probe
from .meta_format import *



__all__ = ["Asset", "asset_by_path", "get_assets"]


class Asset(object):
    def __init__(self, id=False, **kwargs):
        self.kwargs = kwargs
        self._db = kwargs.get("db", False)
        self.id = id
        self.id_storage = 0
        self.path = ""
        self.fsize = 0
        self.ctime = 0
        self.mtime = 0
        self.meta = {}
        self.report = {}

        if id:
            self.load(id)

    @property
    def db(self):
        if not self._db:
            self._db = DB()
        return self._db

    def load(self, id):
        self.db.query("SELECT id_storage, path, fsize, ctime, mtime, meta, report FROM assets WHERE id = %s", [id])
        for row in self.db.fetchall():
            self.id_storage, self.path, self.fsize, self.ctime, self.mtime, self.meta, self.report = row
            break
        else:
            logging.error("Unable to load asset {}".format(id))

    def save(self):
        vals = [self.id_storage, self.path, self.fsize, self.ctime, self.mtime, json.dumps(self.meta), json.dumps(self.report)]
        if not self.id:
            self.db.query("INSERT INTO assets (id_storage, path, fsize, ctime, mtime, meta, report) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id", vals)
            self.id = self.db.fetchone()[0]
        else:
            vals.append(self.id)
            self.db.query("UPDATE assets SET id_storage=%s, path=%s, fsize=%s, ctime=%s, mtime=%s, meta=%s, report=%s WHERE id=%s", vals)
        self.db.commit()


    def __repr__(self):
        return "asset ID {} ({})".format(self.id, self.base_name)

    def __getitem__(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        return self.meta.get(key, None)


    @property
    def base_name(self):
        return get_base_name(self.path)

    def probe(self):
        if not (self.id_storage and self.path):
            return False
        path = get_path(self.id_storage, self.path)
        if not os.path.exists(path):
            return False

        self.meta = probe(path)

    def show(self, key):
        if key in meta_format:
            return meta_format[key](self[key])
        return self[key]

    def has_job(self, id_action):
        return id_action in self.report.get("created_jobs", [])


def asset_by_path(id_storage, path, db=False):
    db = db or DB()
    db.query("SELECT id FROM assets WHERE id_storage=%s AND path=%s", [id_storage, path])
    for  id, in db.fetchall():
        return Asset(id, db=db)
    return False


def get_assets(**kwargs):
    db = kwargs.get("db", DB())
    order = kwargs.get("order", False)
    conds = kwargs.get("conds", [])
    count = kwargs.get("count", False)
    query = "SELECT id, id_storage, path, fsize, ctime, mtime, meta, report"
    if count:
        query += ", COUNT(id) OVER() AS full_count"
    else:
        query += ", 0"

    query += " FROM assets"
    if conds:
        query += " WHERE " + " AND ".join(conds)
    if order:
        query += " ORDER BY " + order
    db.query(query)
    for row in db.fetchall():
        asset = Asset(db=db)
        asset.id, asset.id_storage, asset.path, asset.fsize, asset.ctime, asset.mtime, asset.meta, asset.report, asset.count = row
        yield asset
