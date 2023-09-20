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

#=====================抽卡模块=====================#
# 祈愿规则
@app.route('/gacha/info/<int:id>', methods=['GET'])
def gacha_info(id):

    schedule = {}
    textmap = {
        'title_map': {},
        'item_map': {}
    }
    language = request.args.get('lang') or 'en'
    try:
        f = open(f"{define.GACHA_SCHEDULE_PATH}/{id}.json")                  # 加载当前卡池祈愿规则
        schedule = json.load(f)
        f.close()
    except Exception as err:
        abort(
            404, description=f"Unexpected {err=}, {type(err)=} while loading gacha schedule data for {id=}")
    try:
        f = open(f"{define.GACHA_TEXTMAP_PATH}/{language}.json")            # 加载适配的语言
        textmap = json.load(f)
        f.close()
    except Exception as err:
        print(
            f"Unexpected {err=}, {type(err)=} while loading textmap for {language=}")
    return render_template("gacha/details.tmpl", schedule=schedule, textmap=textmap, id=id), 203

# 祈愿记录
@app.route('/gacha/record/<int:type>', methods=['GET'])
def gacha_log(type):
    return render_template("gacha/history.tmpl"), 203