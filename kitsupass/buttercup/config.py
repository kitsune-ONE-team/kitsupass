import json
import os

CONFIG_PATH = os.path.expanduser('~/.config/buttercup-keyring-server.json')
CONFIG = {}
try:
    with open(CONFIG_PATH, 'r') as f:
        CONFIG = json.load(f)
except IOError:
    pass


def getConfigValue(key):
    return CONFIG.get(key)


def setConfigValue(key, value):
    CONFIG[key] = value

    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(CONFIG, f, indent=4)
    except IOError:
        pass
