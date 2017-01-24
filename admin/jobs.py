from cherryadmin import CherryAdminView
from smartcoder import *

class ViewJobs(CherryAdminView):
    def build(self, *args, **kwargs):

        try:
            current_view = args[1]
            if current_view not in ["active", "failed", "completed"]:
                raise ValueError
        except IndexError, ValueError:
            current_view = "active"

        self["primary_column"] = "base_name"
        self["columns"] = [
                ["base_name", "Title"],
                ["action_title", "Action"],
                ["progress", "Progress"],
                ["message", "Status"],
            ]


        conds = ["a.id = j.id_asset"]
        if current_view == "active":
            conds.append("(j.status IN (0, 1, 5 , 6) OR j.end_time > {})".format(time.time() - 300))
        elif current_view == "completed":
            conds.append("j.status = 2")
        elif current_view == "failed":
            conds.append("j.status IN (3, 4)")


        conds = " WHERE " + " AND ".join(conds)
        order = " ORDER BY j.creation_time DESC"

        data = []
        query = """SELECT j.id_asset, j.id_action, a.path, j.status, j.progress, j.message, j.creation_time, j.start_time, j.end_time FROM jobs AS j, assets AS a"""
        query += conds
        query += order

        db = DB()
        db.query(query)

        for id_asset, id_action, path, status, progress, message, ctime, stime, etime in db.fetchall():
            action = actions[id_action]
            row = {
                    "id_action" : id_action,
                    "action_title" : action.title,
                    "base_name" : get_base_name(path),
                    "status" : status,
                    "progress" : progress,
                    "message" : message,
                    "ctime" : ctime,
                    "stime" : stime,
                    "etime" : etime
                }
            data.append(row)
        self["data"] = data
