from cherryadmin import CherryAdminView
from smartcoder import *

class ViewDialogDetail(CherryAdminView):
    def build(self, *args):

        self["args"] = str(args)
