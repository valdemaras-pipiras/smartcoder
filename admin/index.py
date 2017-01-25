import math
import time

from cherryadmin import CherryAdminView
from smartcoder import *

RECORDS_PER_PAGE = 200

class ViewIndex(CherryAdminView):
    def build(self, *args, **kwargs):
        process_start_time = time.time()
        try:
            current_page = int(kwargs["p"])
        except (KeyError, ValueError, TypeError):
            current_page = 1

        self["primary_column"] = "base_name"
        self["columns"] = [
                ["id", "#"],
                ["base_name", "Title"],
                ["timecode", "Start TC"],
                ["duration", "Duration"],
                ["guess_aspect_ratio", "Aspect"],
                ["mtime", "Modified"],
            ]
        data = []


        db = DB()
        for asset in get_assets(
                db=db,
                order="ctime DESC",
                limit=RECORDS_PER_PAGE,
                offset=(current_page - 1)*RECORDS_PER_PAGE
            ):
            data.append(asset)

        self["data"] = data
        self["p"] = current_page
        self["page_count"] = int(math.ceil(data[0].count / RECORDS_PER_PAGE)) if data else 0
        logging.info("Asset view loaded in {:.03f}s".format(time.time() - process_start_time))

