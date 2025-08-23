import base64
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.padding import PKCS7


def encrypt(text: str, password: str) -> str:
    """
    openssl aes-256-cbc -e -pbkdf2 -md sha256 -iter 10000 -a -in text -out data
    """
    salt = os.urandom(8)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=256 // 8 + 16,
        salt=salt,
        iterations=10000,
    )
    secret = kdf.derive(password.encode())
    key = secret[:256 // 8]
    iv = secret[256 // 8:]

    encryptor = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
    ).encryptor()
    padder = PKCS7(128).padder()

    raw = padder.update(text.encode()) + padder.finalize()
    raw = encryptor.update(raw) + encryptor.finalize()

    data = base64.b64encode(b'Salted__' + salt + raw).decode()
    i = 0
    multiline = ''
    while True:
        chunk = data[i:i + 64]
        if chunk:
            multiline += chunk + '\n'
        else:
            break
        i += 64
    return multiline


def decrypt(data: str, password: str) -> str:
    """
    openssl aes-256-cbc -d -pbkdf2 -md sha256 -iter 10000 -a -in data
    """
    raw = base64.b64decode(data)
    if raw[:8] != b'Salted__':
        return

    salt = raw[8:16]
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=256 // 8 + 16,
        salt=salt,
        iterations=10000,
    )
    secret = kdf.derive(password.encode())
    key = secret[:256 // 8]
    iv = secret[256 // 8:]

    decryptor = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
    ).decryptor()
    unpadder = PKCS7(128).unpadder()

    text = decryptor.update(raw[16:]) + decryptor.finalize()
    text = unpadder.update(text) + unpadder.finalize()
    return text.decode()
