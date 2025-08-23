CONFIG = {}


def getConfigValue(key):
    return CONFIG.get(key)


def setConfigValue(key, value):
    CONFIG[key] = value


class Notify:
    class Notification:
        def __init__(self, title, msg, type):
            self.title = title
            self.msg = msg
            self.type = type

        @classmethod
        def new(cls, title, msg, type):
            notification = cls(title, msg, type)
            Notify.notification = notification
            return notification

        def set_timeout(self, t):
            pass

        def show(self):
            pass


class Storage:
    def __init__(self):
        self.data = {}

    def open(self):
        pass

    def create(self):
        pass

    def insert(self, name, data):
        self.data[name] = data

    def edit(self, name, data):
        self.data[name] = data

    def show(self, name = ''):
        return self.data[name]

    def delete(self, name):
        self.data.pop(name, None)

    def move(self, name, new_name):
        self.data[new_name] = self.data.pop(name)

    def copy(self, name, new_name):
        self.data[new_name] = self.data[name]

    def find(self, name = ''):
        for k, v in self.data:
            if name in k:
                yield v


from kitsupass.buttercup import config
config.getConfigValue = getConfigValue
config.setConfigValue = setConfigValue

from kitsupass.buttercup import api
api.Notify = Notify
