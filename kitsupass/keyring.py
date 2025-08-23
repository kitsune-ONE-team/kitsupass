import uuid

try:
    import secretstorage
except ImportError:
    secretstorage = None


def save_password(id: uuid.UUID, password: str) -> None:
    if not secretstorage:
        return

    dbus_connection = secretstorage.dbus_init()
    collection = secretstorage.get_default_collection(dbus_connection)
    if collection.is_locked():
        collection.unlock()
    collection.create_item(f'kitsupass://{id}', {
        'application': 'kitsupass',
        'username': str(id),
        'URL': f'kitsupass://{id}',
    }, password)
    dbus_connection.close()


def remove_password(id: uuid.UUID) -> None:
    if not secretstorage:
        return

    dbus_connection = secretstorage.dbus_init()
    collection = secretstorage.get_default_collection(dbus_connection)
    if collection.is_locked():
        collection.unlock()
    for item in collection.search_items({'URL': f'kitsupass://{id}'}):
        password = item.delete()
    dbus_connection.close()


def load_password(id: uuid.UUID) -> str | None:
    if not secretstorage:
        return

    password = None
    dbus_connection = secretstorage.dbus_init()
    collection = secretstorage.get_default_collection(dbus_connection)
    if collection.is_locked():
        collection.unlock()
    for item in collection.search_items({'URL': f'kitsupass://{id}'}):
        password = item.get_secret().decode()
        break
    dbus_connection.close()
    return password
