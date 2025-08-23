import json

from bottle import abort, HTTPResponse

from .auth import encryptAPIPayload


def respondJSON(request, obj: dict):
    clientID = request.clientID
    if not clientID:
        return abort(403, 'No client ID set: Invalid response state')

    data = encryptAPIPayload(clientID, json.dumps(obj).encode())
    headers = {
        'X-Bcup-API': 'enc,1',
        'Content-Type': 'text/plain',
        'X-Content-Type': 'application/json',
    }
    return HTTPResponse(status=200, body=data.encode(), headers=headers)
