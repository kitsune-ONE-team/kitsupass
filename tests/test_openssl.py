import base64
import subprocess
import unittest

from kitsupass.context import TMP
from kitsupass.openssl import encrypt, decrypt


class TestOpenSSL(unittest.TestCase):
    def test_encrypt_decrypt(self):
        password = 'password'

        data = encrypt('plaintext', password)
        self.assertEqual(base64.b64decode(data)[:8], b'Salted__')

        text = decrypt(data, password)
        self.assertEqual(text, 'plaintext')

    def test_kitsupass2openssl(self):
        password = 'password'

        with TMP() as tmp:
            with open(tmp.name, 'w') as f:
                f.write(encrypt('plaintext', password))

            openssl = subprocess.Popen(
                f'openssl aes-256-cbc -d -pbkdf2 -md sha256 -iter 10000 -a -in {tmp.name} -pass pass:{password}',
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            text, _ = openssl.communicate()
            self.assertEqual(text.decode(), 'plaintext')

    def test_openssl2kitsupass(self):
        password = 'password'

        with TMP() as tmp:
            with open(tmp.name, 'w') as f:
                f.write('plaintext')

            openssl = subprocess.Popen(
                f'openssl aes-256-cbc -e -pbkdf2 -md sha256 -iter 10000 -a -in {tmp.name} -pass pass:{password}',
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            data, _ = openssl.communicate()
            self.assertEqual(decrypt(data.decode(), password), 'plaintext')
