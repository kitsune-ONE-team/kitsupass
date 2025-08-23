import gi
import os
import re
import subprocess
import sys

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from .exception import NotFoundStorageError
from .getpass import getpass
from .storage import Storage

RESPONSE_TYPE_RESET = 1
RESPONSE_TYPE_SAVE = 2


def confirm(request):
    dialog = Gtk.MessageDialog(
        message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.YES_NO,
        text='SSH',
    )
    dialog.format_secondary_text(request)

    response = dialog.run()
    dialog.destroy()

    if response == Gtk.ResponseType.YES:
        print('yes')
        sys.exit(0)

    elif response == Gtk.ResponseType.NO:
        print('no')
        sys.exit(0)

    else:
        sys.exit(1)


def fetchpass(request, name, storage, username=None, keypath=None):
    names = tuple(storage.find(name))
    if username:
        for cur_name in names:
            item = storage.show(cur_name)
            for line in item.split('\n'):
                if line.startswith('username:'):
                    k, _, v = line.partition(':')
                    if username == v.strip():
                        break
        else:
            item = storage.show((names + (name,))[0])
    else:
        item = storage.show(name)

    dialog = Gtk.MessageDialog(
        message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.YES_NO,
        text='SSH',
    )
    dialog.format_secondary_text(request)
    dialog.add_button('Reset', RESPONSE_TYPE_RESET)
    if keypath:
        dialog.add_button('Save', RESPONSE_TYPE_SAVE)

    response = dialog.run()
    dialog.destroy()

    if response == Gtk.ResponseType.YES:
        print(item.split('\n')[0])
        sys.exit(0)

    elif response == Gtk.ResponseType.NO:
        sys.exit(1)

    elif response == RESPONSE_TYPE_RESET:
        storage.delete(name)
        raise NotFoundStorageError

    elif response == RESPONSE_TYPE_SAVE:
        subprocess.run(['ssh-add', keypath])
        print(item.split('\n')[0])
        sys.exit(0)


def askpass(request, name=None, storage=None, username=None):
    password = getpass('SSH', request)
    if password:
        if name and storage:
            data = password
            if username:
                data += f'\nusername: {username}'
            storage.insert(name, data)

        sys.exit(0)

    else:
        sys.exit(1)


def checkpass(request, name, username=None, keypath=None):
    storage = Storage(has_gui=True)
    storage.open()

    try:
        fetchpass(request, name, storage=storage, username=username, keypath=keypath)
    except NotFoundStorageError:
        askpass(request, name, storage=storage, username=username)


def main():
    try:
        request = sys.argv[1].strip()
    except IndexError:
        request = ''

    # open('/tmp/kp.txt', 'w').write(request)

    if m := re.match(r"Enter passphrase for key '([^']+)':", request):
        key_path = m.group(1)
        dot_ssh = os.path.expanduser('~/.ssh/')
        if key_path.startswith(dot_ssh):
            key_name = key_path[len(dot_ssh):]
            checkpass(request, f'ssh:{key_name}', keypath=key_path)

    elif m := re.match(r"Enter passphrase for ([^']+):", request):
        key_path = m.group(1)
        dot_ssh = os.path.expanduser('~/.ssh/')
        if key_path.startswith(dot_ssh):
            key_name = key_path[len(dot_ssh):]
            checkpass(request, f'ssh:{key_name}', keypath=key_path)

    elif m := re.match(r'\(([^()]+)\) Password for ([^:]+):', request):
        name = m.group(1)
        if '@' in name:
            username, _, hostname = name.partition('@')
            checkpass(request, hostname, username=username)

    elif m := re.match(r"The authenticity of host '([^']+)' can't be established.*", request):
        confirm(request)

    else:
        askpass(request)

    print('To use kitsupass-askpass, please set the following environment variables:')
    print('SSH_ASKPASS=kitsupass-askpass')
    print('SSH_ASKPASS_REQUIRE=force')


if __name__ == '__main__':
    main()
