import time
import thread

__all__ = ["SystemMonitor"]



class SystemMonitor(object):
    def __init__(self):
        self.to_watch = []
        thread.start_new_thread(self.work, ())

    def send_alert(self, obj):
        pass

    def work(self):
        while True:
            for obj in self.to_watch:
                if not obj.is_working:
                    #TODO
                    self.send_alert(obj)
            time.sleep(60)

    def watch(self, obj):
        self.to_watch.append(obj)


