from gi.repository import Notify

# import secretstorage

from bottle import Bottle
# from jeepney.io.blocking import DBusConnection

from .auth import generateBrowserKeys
from .symbols import BROWSER_API_HOST_PORT
from ..storage import Storage


class Application(Bottle):
    storage: Storage | None
    auth_code: int | None
    # dbus_connection: DBusConnection
    storage: Storage | None

    def __init__(self) -> None:
        super().__init__()
        self.auth_code = None
        self.storage = None
        appid = f'{self.__class__.__module__}.{self.__class__.__name__}'
        Notify.init(appid)

    def set_code(self, code: str = None) -> None:
        del self.auth_code
        self.auth_code = code

    def create(self, storage: Storage) -> None:
        del self.storage
        self.storage = storage

    def run(self) -> None:
        generateBrowserKeys()
        # self.dbus_connection = secretstorage.dbus_init()
        super().run(host='localhost', port=BROWSER_API_HOST_PORT)

    def close(self):
        # self.dbus_connection.close()
        # del self.dbus_connection
        pass


app = Application()
