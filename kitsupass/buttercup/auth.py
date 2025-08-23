import base64
import codecs
import os
import random
import string

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from jwskate import Jwk

from .config import getConfigValue, setConfigValue
from .symbols import API_KEY_ALGO, API_KEY_CURVE


def generateBrowserKeys():
    privateKeyData = getConfigValue('browserPrivateKey')
    publicKeyData = getConfigValue('browserPublicKey')
    if privateKeyData and publicKeyData:
        return
    privateKey = Jwk.generate(kty=API_KEY_ALGO[:2], crv=API_KEY_CURVE)
    publicKey = privateKey.public_jwk()
    setConfigValue('browserPrivateKey', privateKey.to_dict())
    setConfigValue('browserPublicKey', publicKey.to_dict())


def deriveSecretKey(privateKey: dict, publicKey: dict) -> bytes:
    secret = Jwk(privateKey).cryptography_key.exchange(
        getattr(ec, API_KEY_ALGO)(),
        Jwk(publicKey).cryptography_key,
    )
    return codecs.encode(secret, 'hex')


def decryptAPIPayload(clientID, payload: str) -> bytes:
    clients = getConfigValue('browserClients')
    clientConfig = clients[clientID]
    browserPrivateKey = getConfigValue('browserPrivateKey')
    secret = deriveSecretKey(browserPrivateKey, clientConfig)

    content, iv, salt, auth, roundsRaw, methodRaw = payload.split('$')
    method = getattr(modes, methodRaw.upper())
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=256 // 8,
        salt=salt.encode(),
        iterations=int(roundsRaw),
    )

    decryptor = Cipher(
        algorithms.AES(kdf.derive(secret)),
        method(codecs.decode(iv, 'hex'), tag=codecs.decode(auth, 'hex')),
    ).decryptor()
    decryptor.authenticate_additional_data(f'{iv}{salt}'.encode())
    return decryptor.update(base64.b64decode(content)) + decryptor.finalize()


def encryptAPIPayload(clientID, payload: bytes) -> str:
    clients = getConfigValue('browserClients')
    clientConfig = clients[clientID]
    browserPrivateKey = getConfigValue('browserPrivateKey')
    secret = deriveSecretKey(browserPrivateKey, clientConfig)

    iv = codecs.encode(os.urandom(16), 'hex').decode()
    salt = ''.join([random.choice(string.ascii_letters) for i in range(12)])
    rounds = 100000
    method = modes.GCM
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=256 // 8,
        salt=salt.encode(),
        iterations=rounds,
    )

    encryptor = Cipher(
        algorithms.AES(kdf.derive(secret)),
        method(codecs.decode(iv, 'hex')),
    ).encryptor()
    encryptor.authenticate_additional_data(f'{iv}{salt}'.encode())
    content = encryptor.update(payload) + encryptor.finalize()

    return '$'.join((
        base64.b64encode(content).decode(),
        iv,
        salt,
        codecs.encode(encryptor.tag, 'hex').decode(),
        str(rounds),
        method.__name__.lower(),
    ))
