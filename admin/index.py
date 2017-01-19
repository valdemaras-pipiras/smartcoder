from cherryadmin import CherryAdminView
from smartcoder import *

class ViewIndex(CherryAdminView):
    def build(self, *args, **kwargs):

        self["primary_column"] = "base_name"
        self["columns"] = [
                ["id", "#"],
                ["base_name", "Title"],
                ["guess_aspect_ratio", "Aspect"],
                ["mtime", "Modified"],
                ["status", "Status"],
            ]
        data = []
        db = DB()
        for asset in get_assets(db=db):
            data.append(asset)
        self["data"] = data
