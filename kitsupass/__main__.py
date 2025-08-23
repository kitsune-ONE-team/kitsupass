import argparse
import getpass
import os
import subprocess
import sys
import uuid

from importlib.resources import files
from urllib.parse import parse_qs, urlparse

import pyotp

from .context import TMP
from .storage import Storage

BIN_PATH = os.path.expanduser('~/.local/bin')
SYSTEMD_PATH = os.path.expanduser('~/.config/systemd/user')
VERSION = (0, 0, 1)
LOGO_PIX = '''
   ▄▄▄          ▄▄▄
   █  ▀  ▄▄▄▄  ▀  █
   ▀  ▄▀      ▀▄  ▀
     ▀          ▀
  ▄▀              ▀▄
  ▀▄  ▄█▄    ▄█▄  ▄▀
     ▄ ▀      ▀ ▄
      ▀        ▀
        █    █
         ▀▀▀▀
'''
LOGO_TXT = '''
   |⟍ ____ ⟋|
   |⟋      ⟍|
  ⟋          ⟍
  ⟍  ♦    ♦  ⟋
    ⟍      ⟋
      \\___/
'''


def cmd_init():
    storage = Storage(has_terminal=True)
    storage.create()


def cmd_show():
    storage = Storage(has_terminal=True)
    storage.open()
    try:
        print(storage.show(sys.argv[2]))
    except IndexError:
        print(storage.show())


def cmd_otp():
    storage = Storage(has_terminal=True)
    storage.open()
    item = storage.show(sys.argv[2])
    for line in item.split('\n'):
        if line.startswith('TOTP:'):
            key, _, value = line.partition(':')
            url = urlparse(value.strip())
            query = parse_qs(url.query)
            totp = pyotp.TOTP(query['secret'][0])
            print(totp.now())


def cmd_find():
    name = sys.argv[2]

    storage = Storage(has_terminal=True)
    storage.open()
    for item in storage.find(name):
        print(item)


def cmd_insert():
    name = sys.argv[2]

    with TMP() as tmp:
        subprocess.run([os.getenv('EDITOR'), tmp.name])
        with open(tmp.name, 'r') as f:
            data = f.read()

    storage = Storage(has_terminal=True)
    storage.open()
    storage.insert(name, data)


def cmd_edit():
    name = sys.argv[2]

    storage = Storage(has_terminal=True)
    storage.open()

    with TMP() as tmp:
        with open(tmp.name, 'w') as f:
            f.write(storage.show(name))

        subprocess.run([os.getenv('EDITOR'), tmp.name])
        with open(tmp.name, 'r') as f:
            data = f.read()

    storage = Storage(has_terminal=True)
    storage.open()
    storage.edit(name, data)


def cmd_delete():
    name = sys.argv[2]

    storage = Storage(has_terminal=True)
    storage.open()
    storage.delete(name)


def cmd_move():
    name = sys.argv[2]
    new_name = sys.argv[3]

    storage = Storage(has_terminal=True)
    storage.open()
    storage.move(name, new_name)


def cmd_copy():
    name = sys.argv[2]
    new_name = sys.argv[3]

    storage = Storage(has_terminal=True)
    storage.open()
    storage.copy(name, new_name)


def cmd_enable():
    name = sys.argv[2]
    if name == 'buttercup':
        filename = f'kitsupass-{name}.service'
        filepath = os.path.join(SYSTEMD_PATH, filename)

        if not os.path.exists(SYSTEMD_PATH):
            os.makedirs(SYSTEMD_PATH)

        with open(filepath, 'w') as f:
            package = files(f'kitsupass.{name}')
            for line in package.joinpath(filename).read_text().split('\n'):
                if line.startswith('ExecStart='):
                    key, _, value = line.partition('=')
                    line = f'{key}={BIN_PATH}/{value}'
                f.write(line + '\n')


def cmd_disable():
    name = sys.argv[2]
    if name == 'buttercup':
        filename = f'kitsupass-{name}.service'
        filepath = os.path.join(SYSTEMD_PATH, filename)

        if os.path.exists(filepath):
            os.remove(filepath)


def cmd_version():
    version: str = '.'.join(map(str, VERSION))
    logo = LOGO_PIX if os.getenv('TERM') == 'linux' else LOGO_TXT
    print(f'kitsupass v{version}')
    print(logo.strip('\n'))


def cmd_usage():
    print('''Usage:
    kitsupass init
        Initialize new password storage and set a password for encryption.
        Reencrypt existing password storage using a new password.
    kitsupass [ls] [subfolder]
        List passwords.
    kitsupass find pass-names...
    	List passwords that match pass-names.
    kitsupass [show] pass-name
        Show existing password.
    kitsupass otp pass-name
        Generate an OTP code.
    kitsupass insert pass-name
        Insert new password using your preferred editor.
    kitsupass edit pass-name
        Insert a new password or edit an existing one using your preferred editor.
    kitsupass rm pass-name
        Remove existing password.
    kitsupass mv old-path new-path
        Renames or moves old-path to new-path.
    kitsupass cp old-path new-path
        Copies old-path to new-path.
    kitsupass help
        Show this text.
    kitsupass version
        Show version information.''')


def main():
    try:
        if sys.argv[1] == 'init':
            cmd_init()
        elif sys.argv[1] in ('show', 'ls', 'list'):
            cmd_show()
        elif sys.argv[1] in ('find', 'search'):
            cmd_find()
        elif sys.argv[1] in ('insert', 'add'):
            cmd_insert()
        elif sys.argv[1] == 'edit':
            cmd_edit()
        elif sys.argv[1] in ('delete', 'rm', 'remove'):
            cmd_delete()
        elif sys.argv[1] in ('rename', 'mv'):
            cmd_move()
        elif sys.argv[1] in ('copy', 'cp'):
            cmd_copy()
        elif sys.argv[1] == 'version':
            cmd_version()
        elif sys.argv[1] == 'otp':
            cmd_otp()
        elif sys.argv[1] == 'enable':
            cmd_enable()
        elif sys.argv[1] == 'disable':
            cmd_disable()
        elif sys.argv[1] == 'buttercup':
            from .buttercup.api import app as buttercup_app
            storage = Storage(has_gui=True)
            storage.open()
            buttercup_app.create(storage=storage)
            buttercup_app.run()
            buttercup_app.close()
        else:
            cmd_version()
            cmd_usage()

    except IndexError:
        cmd_show()


if __name__ == '__main__':
    main()
