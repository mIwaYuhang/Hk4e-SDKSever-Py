import yaml
import settings.define as define

from flask import g

def load_config():
    with open(define.CONFIG_FILE_PATH, encoding='utf-8') as file:
        return yaml.safe_load(file)

def get_config():
    config = getattr(g, '_config', None)
    if config is None:
        with open(define.CONFIG_FILE_PATH, encoding='utf-8') as file:
            config = g._config = load_config()
    return config