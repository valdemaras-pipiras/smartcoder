from nxtools import *
from cherryadmin import CherryAdmin

from .index import ViewIndex

__all__ = ["CherryAdmin", "admin_config", "admin_site_context"]

def login_helper(login, password):
    return {"login" : "admin"}

admin_site_context = {
	"name" : "smartcoder",

	"js" : [
		"/static/js/vendor.min.js",
		"/static/js/main.js"
	    ],

	"css" : [
		"/static/css/main.css"
	    ],

	"system_pages" : [
		["system_nodes", "Nodes"],
		["system_profiles", "Profiles"],
		["system_storages", "Storages"],
		["system_watchfolders", "Watchfolders"],
		["system_users", "Users"],
	    ],
    }



def site_context_helper():
    return admin_site_context

def page_context_helper():
    return {}

admin_config = {
        "host" : "127.0.0.1",
        "port" : 8086,

        "static_dir" : "admin/static",
        "templates_dir" : "admin/templates",
        "login_helper" : login_helper,
        "site_context_helper" : site_context_helper,
        "page_context_helper" : page_context_helper,
        "blocking" : True,
        "views" : {
                "index" : ViewIndex,
            },
        "api_methods" : {

            }
    }
