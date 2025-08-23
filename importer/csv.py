import copy
import csv
import os
import sys

from urllib.parse import urlparse

from kitsupass.storage import Storage


def main():
    storage = Storage(has_terminal=True)
    storage.open()

    with open(sys.argv[1], 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            attributes = {}
            password = ''
            for k, v in row.items():
                if k.startswith('!') or k == 'id' or not v:
                    continue

                if k == 'password':
                    password = v
                    continue

                if k.lower() == 'url':
                    attributes['URL'] = v
                    continue

                attributes[k] = v

            url = urlparse(attributes.get('URL'))
            name = url.netloc
            if not name:
                continue

            data = f'{password}\n'
            if 'username' in attributes:
                data += f'username: {attributes.pop("username")}\n'
            if 'URL' in attributes:
                data += f'URL: {attributes.pop("URL")}\n'
            if 'title' in attributes:
                data += f'title: {attributes.pop("title")}\n'
            for k, v in attributes.items():
                data += f'{k}: {v}\n'

            storage.insert(name, data)


if __name__ == '__main__':
    main()
