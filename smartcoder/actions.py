import os
import time

from nxtools import *

from .common import *
from .db import *

__all__ = ["Action"]

class Action():
    def __init__(self, id, title, settings, **kwargs):
        self.db = kwargs.get("db", DB())
        self.id = id
        self.title = title
        self.settings = xml(settings)

        try:
            self.allow_if = self.settings.find("allow_if")
            if self.allow_if is not None:
                self.allow_if = self.allow_if.text
        except Exception:
            log_traceback()
            self.allow_if = None

        try:
            self.create_if = self.settings.find("create_if")
            if self.create_if is not None:
                self.create_if = self.create_if.text
        except Exception:
            log_traceback()
            self.create_if = None

        try:
            self.start_if = self.settings.find("start_if")
            if self.start_if is not None:
                self.start_if = self.start_if.text
        except Exception:
            log_traceback()
            self.start_if = None

    def __repr__(self):
        return "action {}".format(self.title)

    def should_allow(self, asset):
        if not self.allow_if:
            return False
        return eval(self.allow_if)

    def should_create(self, asset):
        if not self.create_if:
            return False
        return eval(self.create_if)

    def should_start(self, asset):
        if not self.start_if:
            return False
        return eval(self.start_if)

