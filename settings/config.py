import json
import settings.define as define

from flask import g
from settings.config import load_config

def load_config():
    with open(define.CONFIG_FILE_PATH, encoding='utf-8') as file:
        return json.load(file)


def get_config():  # config is reloadable per-request except for "app" section
    config = getattr(g, '_config', None)
    if config is None:
        with open(define.CONFIG_FILE_PATH, encoding='utf-8') as file:
            config = g._config = load_config()
    return config
