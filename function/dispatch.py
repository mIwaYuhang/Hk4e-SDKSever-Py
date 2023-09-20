from __main__ import app
from flask import request, send_from_directory, abort, render_template, flash, current_app
from flask_mail import Message
from flask_caching import Cache
import random
import string
import json
import re
from time import time as epoch
from settings.response import json_rsp, json_rsp_with_msg
from settings.database import get_db
from settings.crypto import decrypt_rsa_password, decrypt_sdk_authkey
from settings.utils import forward_request, request_ip, get_country_for_ip, password_hash, password_verify, mask_string, mask_email
import settings.define as define
from settings.config import get_config
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
@app.context_processor
def inject_config():
    config = get_config()
    return {'config': config}

#=====================Dispatch配置=====================#
# 全局dispatch
@app.route('/query_region_list', methods=['GET'])
def query_region_list():
    try:
        return forward_request(request, f"{get_config()['dispatch']['global']}/query_region_list?{request.query_string.decode()}")
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=} while forwarding request")
        abort(500)

# 解析dispatch
@app.route('/query_region/<name>', methods=['GET'])
def query_cur_region(name):
    try:
        return forward_request(request, f"{get_config()['dispatch']['local'][name]}/query_cur_region?{request.query_string.decode()}")
    except KeyError:
        print(f"未知的region={name}")
        abort(404)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=} while forwarding request")
        abort(500)