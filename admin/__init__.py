from nxtools import *
from cherryadmin import CherryAdmin

from smartcoder import *

from .index import ViewIndex
from .jobs import ViewJobs

__all__ = ["CherryAdmin", "admin_config", "admin_site_context"]

def login_helper(login, password):
    db = DB()
    db.query("SELECT id, is_admin FROM users WHERE login=%s AND password=%s", [login, hash_password(password)])
    for id, is_admin in db.fetchall():
        return {
                "id" : id,
                "login" : login,
                "is_admin" : is_admin
            }
    return False

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
                "jobs" : ViewJobs,
            },
        "api_methods" : {

            }
    }
