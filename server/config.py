import json
import os.path
import os

_config = {
    'cache': {
        'html': './html_cache/',
    },
    'package': {
        'future': './future/',
        'latest': './latest/',
    }
}

def init(path=os.path.expanduser('~') + '/.config/mmmrc'):
    global _config
    prefix, _ = os.path.split(path)
    if not os.path.exists(prefix):
        os.makedirs(prefix)
    if os.path.exists(path):
        configfile = open(path, "r+")
        _config = json.load(configfile)
    else:
        configfile = open(path, "w+")
        json.dump(_config, configfile)

def section(section):
    return _config[section]

