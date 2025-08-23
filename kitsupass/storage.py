import os
import shutil
import subprocess
import uuid

from getpass import getpass

from . import exception
from .keyring import save_password, load_password, remove_password
from .openssl import encrypt, decrypt

STORAGE_PATH = os.path.expanduser('~/.local/share/kitsupass')


class Storage:
    def __init__(self, has_terminal: bool = False, has_gui: bool = False):
        self.has_terminal = has_terminal
        self.has_gui = has_gui
        self.path = os.getenv('KITSUPASS_PATH', STORAGE_PATH)
        self.password = None

    @property
    def is_open(self) -> bool:
        return bool(self.password)

    def open(self):
        for filename in os.listdir(self.path):
            if filename.startswith('.urn:uuid:'):
                self.id = uuid.UUID(filename.rpartition(':')[-1])
                id_path = os.path.join(self.path, filename)
                break

        else:
            raise exception.WrongStorageError

        initial_password = load_password(self.id)
        password = initial_password

        if not password and self.has_terminal:
            password = getpass('Enter the primary vault password: ')

        if not password and self.has_gui:
            password = subprocess.check_output([
                'python', '-m', 'kitsupass.getpass',
                'Enter the primary vault password',
            ]).decode().strip('\n').strip()

        if not password:
            raise exception.InvalidPasswordStorageError

        with open(id_path, 'r') as f:
            try:
                if decrypt(f.read(), password or '') != str(self.id):
                    raise exception.InvalidPasswordStorageError
            except ValueError:
                raise exception.InvalidPasswordStorageError

        if not initial_password:
            save_password(self.id, password)
        self.password = password

    def close(self):
        remove_password(self.id)
        self.password = None

    def create(self):
        if os.path.exists(self.path):
            raise exception.ExistingStorageError

        self.password = getpass('Enter a new primary vault password: ')
        if self.password != getpass('Retype password: '):
            raise exception.UnmatchedPasswordStorageError

        os.makedirs(self.path)

        self.id = uuid.uuid4()
        id_path = os.path.join(self.path, f'.{self.id.urn}')
        with open(id_path, 'w') as f:
            f.write(encrypt(str(self.id), self.password))

        save_password(self.id, self.password)

    def insert(self, name: str, data: str) -> None:
        if not self.is_open:
            raise exception.LockedStorageError

        orig_path = os.path.join(self.path, name)
        path = orig_path
        i = 2
        while os.path.exists(path):
            path = f'{orig_path} ({i})'
            i += 1

        with open(path, 'w') as f:
            f.write(encrypt(data, self.password))

    def edit(self, name: str, data: str) -> None:
        if not self.is_open:
            raise exception.LockedStorageError

        path = os.path.join(self.path, name)
        if not os.path.exists(path):
            raise exception.NotFoundStorageError

        with open(path, 'w') as f:
            f.write(encrypt(data, self.password))

    def show(self, name: str = '') -> str:
        if not self.is_open:
            raise exception.LockedStorageError

        if name:
            path = os.path.join(self.path, name)
        else:
            path = self.path

        if not os.path.exists(path):
            raise exception.NotFoundStorageError

        if os.path.isdir(path):
            return '\n'.join(self.find(name))

        else:
            with open(path, 'r') as f:
                return decrypt(f.read(), self.password)

    def delete(self, name: str) -> str:
        path = os.path.join(self.path, name)
        if not os.path.exists(path):
            raise exception.NotFoundStorageError

        os.remove(path)

    def move(self, name: str, new_name: str) -> str:
        path = os.path.join(self.path, name)
        if not os.path.exists(path):
            raise exception.NotFoundStorageError

        new_path = os.path.join(self.path, new_name)
        if os.path.exists(new_path):
            raise exception.OverwriteStorageError

        os.rename(path, new_path)

    def copy(self, name: str, new_name: str) -> str:
        path = os.path.join(self.path, name)
        if not os.path.exists(path):
            raise exception.NotFoundStorageError

        new_path = os.path.join(self.path, new_name)
        shutil.copy(path, new_path)

    def find(self, name: str = '') -> str:
        for path, foldernames, filenames in os.walk(self.path):
            for filename in filenames:
                if filename.startswith('.urn:uuid:'):
                    continue
                if name in filename:
                    yield filename
