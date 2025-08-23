class StorageError(Exception):
    pass


class WrongStorageError(StorageError):
    msg = 'Error: invalid password storage.'


class InvalidPasswordStorageError(StorageError):
    msg = 'Error: invalid password.'


class ExistingStorageError(StorageError):
    msg = 'Error: storage exists.'


class LockedStorageError(StorageError):
    msg = 'Error: storage locked.'


class UnmatchedPasswordStorageError(StorageError):
    msg = 'Error: the entered passwords do not match.'


class NotFoundStorageError(StorageError):
    msg = 'Error: item does not exists.'


class OverwriteStorageError(StorageError):
    msg = 'Error: item is already exists.'
