import io
import json
import re

from bottle import abort, request

from .auth import decryptAPIPayload
from .config import getConfigValue


class ButtercupRequest:
    def __init__(self, request):
        self.__request = request
        self.__body = None
        self.__json = None
        self.__headers = {}
        self.clientID = None

    @property
    def body(self):
        return self.__body or self.__request.body

    @body.setter
    def body(self, value):
        self.__body = io.BytesIO(value)

    @property
    def json(self):
        return self.__json or self.__request.json

    @json.setter
    def json(self, value):
        self.__json = value

    @property
    def GET(self):
        return self.__request.GET

    def get_header(self, name):
        return self.__headers.get(name, self.__request.get_header(name))

    def set_header(self, name, value):
        self.__headers[name] = value


def requireClient(method):
    def f(request=request, **kwargs):
        auth = request.get_header('Authorization')
        *_, clientID = re.split(r'\s+', auth)
        clients = getConfigValue('browserClients')

        if clientID not in clients:
            return abort(401, 'No key registered')

        if not isinstance(request, ButtercupRequest):
            request = ButtercupRequest(request)
        request.clientID = clientID

        return method(request=request, **kwargs)
    return f


def requireKeyAuth(method):
    def f(request=request, **kwargs):
        auth = request.get_header('Authorization')
        bodyType = request.get_header('X-Content-Type') or 'text/plain'
        *_, clientID = re.split(r'\s+', auth)

        if not clientID:
            return abort(401, 'No client key provided')

        decryptedStr = decryptAPIPayload(clientID, request.body.read().decode())
        if not isinstance(request, ButtercupRequest):
            request = ButtercupRequest(request)

        if 'application/json' == bodyType:
            request.json = json.loads(decryptedStr)
            request.set_header('Content-Type', bodyType)
        else:
            request.body = decryptedStr

        return method(request=request, **kwargs)
    return f
