import os
import hashlib
from xml.etree import ElementTree as ET

from nxtools import *

PENDING = 0
IN_PROGRESS = 1
FINISHED = 2
ABORTED = 3
FAILED = 4
RESTART_REQUIRED = 5
ABORT_REQUIRED = 6


logging.user = "smartcoder"

config = {
        "db_host" : "localhost",
        "db_user" : "nebula",
        "db_pass" : "nebula",
        "db_name" : "smartcoder",
        "password_salt" : "9a4c587d-26da-42ff-8f57-b8077350e3da"
    }

storages = {}

def hash_password(password):
    return hashlib.sha512(password + config["password_salt"]).hexdigest()

def get_path(id_storage, path):
    id_storage = int(id_storage)
    return os.path.join(storages[id_storage], path)

def xml(data):
    return ET.XML(data)
