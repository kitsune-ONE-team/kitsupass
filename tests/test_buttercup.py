import base64
import json
import random
import string
import subprocess
import unittest

import bottle

from jwskate import Jwk
from webtest import TestApp

from .mock import Notify, Storage, getConfigValue, setConfigValue

from kitsupass.buttercup import api
from kitsupass.buttercup.api import app
from kitsupass.buttercup.auth import (
    generateBrowserKeys, deriveSecretKey, decryptAPIPayload, encryptAPIPayload,
)
from kitsupass.buttercup.symbols import API_KEY_ALGO, API_KEY_CURVE


class TestButtercup(unittest.TestCase):
    def setUp(self):
        self.app = TestApp(app)
        self.app.app.create(storage=Storage())
        bottle.debug(True)

        generateBrowserKeys()
        self.browser_private_key: Jwk = Jwk(getConfigValue('browserPrivateKey'))
        self.browser_public_key: Jwk = Jwk(getConfigValue('browserPublicKey'))

        self.client_id = ''.join((
            random.choice(string.ascii_lowercase + string.digits) for i in range(26)
        ))
        self.client_private_key: Jwk = Jwk.generate(kty=API_KEY_ALGO[:2], crv=API_KEY_CURVE)
        self.client_public_key: Jwk = self.client_private_key.public_jwk()
        setConfigValue('browserClients', {
            self.client_id: self.client_public_key.to_dict(),
        })

    def test_derive_secret_key(self):
        browser_secret = deriveSecretKey(
            self.browser_private_key.to_dict(),
            self.client_public_key.to_dict(),
        )

        client_secret = deriveSecretKey(
            self.client_private_key.to_dict(),
            self.browser_public_key.to_dict(),
        )

        self.assertEqual(browser_secret, client_secret)

    def test_encrypt_decrypt(self):
        data = encryptAPIPayload(self.client_id, b'payload')
        content, iv, salt, auth, rounds, method = data.split('$')
        self.assertEqual(rounds, '100000')
        self.assertEqual(method, 'gcm')

        text = decryptAPIPayload(self.client_id, data)
        self.assertEqual(text, b'payload')

    def test_auth(self):
        response = self.app.post_json('/v1/auth/request', {
            'client': 'test',
            'purpose': 'vaults-access',
            'rev': 1,
        })
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.text, 'OK')

        self.assertEqual(Notify.notification.title, 'Browser Access Request.')
        auth_code = Notify.notification.msg.split(':')[-1].strip()
        self.assertEqual(self.app.app.auth_code, auth_code)

        response = self.app.post_json('/v1/auth/response', {
            'code': auth_code,
            'id': self.client_id,
            'publicKey': self.client_public_key.to_json(),
        })
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.json['publicKey'], self.browser_public_key.to_json())

        headers = {
            'Authorization': f'test {self.client_id}',
            'X-Content-Type': 'application/json',
        }
        request_data = {
            'client': 'test',
            'purpose': 'vaults-access',
            'rev': 1,
        }
        response = self.app.post(
            '/v1/auth/test',
            encryptAPIPayload(self.client_id, json.dumps(request_data).encode()),
            headers=headers,
        )
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.text, 'OK')

    def test_entries(self):
        headers = {
            'Authorization': f'test {self.client_id}',
        }
        response = self.app.get('/v1/entries?type=term&term=test', headers=headers)
        self.assertEqual(response.status_int, 200)
        self.assertEqual(json.loads(decryptAPIPayload(self.client_id, response.text)), {'results': []})

        headers = {
            'Authorization': f'test {self.client_id}',
        }
        response = self.app.get('/v1/entries?type=url&url=https://test.example.com', headers=headers)
        self.assertEqual(response.status_int, 200)
        self.assertEqual(json.loads(decryptAPIPayload(self.client_id, response.text)), {'results': []})
