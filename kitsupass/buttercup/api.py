import random
import string

from urllib.parse import urlparse, urlunparse

from bottle import Bottle, request, abort
from jwskate import Jwk
from gi.repository import Notify

from .. import exception
from .application import app
from .config import getConfigValue, setConfigValue
from .models import (
    AuthRequestSchema,
    AuthResponseSchema,
    EntriesSearchBodySchema,
    SaveNewEntryPayloadSchema,
    TermEntriesSearchQuerySchema,
    UrlEntriesSearchQuerySchema,
)
from .middleware import requireClient, requireKeyAuth
from .response import respondJSON
from .symbols import API_KEY_ALGO, API_KEY_CURVE, FACADE_VERSION


def _get_items(names):
    results = []

    for name in names:
        result = {
            'entryType': 'website',
            'groupID': '0',
            'id': name,
            'properties': {
                'title': name,
                'Note': '',
            },
            'tags': [],
            'sourceID': str(app.storage.id),
            'urls': [],
            'vaultID': str(app.storage.id),
        }

        try:
            item = app.storage.show(name)
            lines = item.split('\n')
            result['properties']['password'] = lines[0].strip()
            for line in lines[1:]:
                if line.startswith('URL: '):
                    result['properties']['URL'] = line.partition(':')[2].strip()
                # elif line.startswith('title: '):
                #     result['properties']['title'] = line.partition(':')[2]
                elif line.startswith('username: '):
                    result['properties']['username'] = line.partition(':')[2].strip()
                else:
                    result['properties']['Note'] += f'{line}\n'
        except exception.LockedStorageError:
            pass

        results.append(result)

    return results


@app.post('/v1/auth/request')
def processAuthRequest(request=request):
    try:
        s = AuthRequestSchema(**request.json)
    except ValueError as e:
        return abort(400, str(e))

    app.set_code(''.join((
        random.choice(string.ascii_uppercase + string.digits) for i in range(12)
    )))
    title = 'Browser Access Request.'
    msg = (
        f'A new connection has been made to this application, '
        f'requesting remote access to all desktop vaults (while unlocked). '
        f'Use the following code to authorise it: {app.auth_code}'
    )
    print(title)
    print(msg)
    notification = Notify.Notification.new(title, msg, 'dialog-information')
    notification.set_timeout(0)
    notification.show()
    return 'OK'


@app.post('/v1/auth/response')
def processAuthResponse(request=request):
    try:
        s = AuthResponseSchema(**request.json)
    except ValueError as e:
        return abort(400, str(e))

    if app.auth_code and app.auth_code == s.code:
        app.set_code()
        clients = getConfigValue('browserClients') or {}
        setConfigValue('browserClients', clients | {
            s.id: s.get_public_key_jwk().to_dict(),
        })
        return {
    	    'publicKey': Jwk(getConfigValue('browserPublicKey')).to_json(),
        }
    abort(403)


@app.post('/v1/auth/test')
@requireClient
@requireKeyAuth
def handleAuthPing(request=request):
    try:
        s = AuthRequestSchema(**request.json)
    except ValueError:
        return abort(400)
    return 'OK'


@app.get('/v1/entries')
@requireClient
def searchEntries(request=request):
    try:
        s = (TermEntriesSearchQuerySchema | UrlEntriesSearchQuerySchema)(**dict(request.GET))
    except ValueError as e:
        return abort(400, str(e))

    names = []

    if s.type == 'term':
        names = app.storage.find(s.term)

    if s.type == 'url':
        names = tuple()
        url = urlparse(s.url)
        domain = url.netloc
        while not names and '.' in domain:
            names = tuple(app.storage.find(domain))
            domain = domain.partition('.')[2]

    return respondJSON(request, {
        'results': _get_items(names),
    })


@app.post('/v1/entries/specific')
@requireClient
@requireKeyAuth
def searchSpecificEntries(request=request):
    try:
        s = EntriesSearchBodySchema(**request.json)
    except ValueError as e:
        return abort(400, str(e))
    names = []

    for entry in s.entries:
        if entry.sourceID == str(app.storage.id):
            similar_names = tuple(app.storage.find(entry.entryID))
            if s.entryID in similar_names:
                names.append(entry.entryID)

    return respondJSON(request, {
        'results': _get_items(names),
    })


@app.get('/v1/otps')
@requireClient
def getAllOTPs(request=request):
    results = []
    for name in app.storage.find('otp:'):
        result = {
            'sourceID': str(app.storage.id),
            'entryID': name,
            'entryProperty': 'TOTP',
            'entryTitle': name,
            'loginURL': None,
            'otpURL': None,
        }

        try:
            item = app.storage.show(name)
            lines = item.split('\n')
            for line in lines[1:]:
                if line.startswith('URL: '):
                    result['loginURL'] = line.partition(':')[2].strip()
                elif line.startswith('TOTP: '):
                    result['otpURL'] = line.partition(':')[2].strip()
        except exception.LockedStorageError:
            pass

        results.append(result)

    return respondJSON(request, {
        'otps': results,
    })


@app.get('/v1/vaults')
@requireClient
def getVaults(request=request):
    return respondJSON(request, {
        'sources': [{
            'id': str(app.storage.id),
            'name': app.storage.__class__.__name__,
            'state': 'unlocked' if app.storage.is_open else 'locked',
            'type': 'file',
            'order': 0,
            'format': 'a',
        }],
    })


@app.get('/v1/vaults-tree')
@requireClient
def getVaultsTree(request=request):
    return respondJSON(request, {
        'tree': {
            str(app.storage.id): {
                '_tag': str(app.storage.id),
                '_ver': FACADE_VERSION,
                'type': 'vault',
                'id': str(app.storage.id),
                'attributes': {},
                'groups': [{
                    'type': 'group',
                    'id': '0',
                    'title': 'Default',
                    'attributes': {},
                    'parentID': str(app.storage.id),
                }],
                'entries': [{
                    'id': item,
                    'type': 'website',
                    'parentID': '0',
                } for item in app.storage.find()],
            }
        },
        'names': {
            str(app.storage.id): app.storage.__class__.__name__,
        },
    })


@app.post('/v1/vaults/<id>/group/<gid>/entry')
@requireClient
@requireKeyAuth
def saveNewEntry(id, gid, request=request):
    try:
        s = SaveNewEntryPayloadSchema(**request.json)
    except ValueError as e:
        return abort(400, str(e))

    # print(s.type)
    # print(s.properties)


@app.post('/v1/vaults/<id>/lock')
@requireClient
def promptVaultLock(id, request=request):
    if str(app.storage.id) == id:
        app.storage.close()


@app.post('/v1/vaults/<id>/unlock')
@requireClient
def promptVaultUnlock(id, request=request):
    if str(app.storage.id) == id:
        app.storage.open()
