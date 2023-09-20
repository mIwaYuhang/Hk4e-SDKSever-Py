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

#=====================支付模块=====================#
# 支付窗口-美元(我怎么没抓到过这个？)
@app.route('/hk4e_cn/mdk/shopwindow/shopwindow/listPriceTier', methods=['POST'])
@app.route('/hk4e_global/mdk/shopwindow/shopwindow/listPriceTier', methods=['POST'])
def price_tier_serve():
    f = open(define.SHOPWINDOW_TIERS_PATH)
    tiers = json.load(f)
    f.close()
    currency = 'USD'
    return json_rsp_with_msg(define.RES_SUCCESS, "OK", {
        "data": {
            "suggest_currency": currency,
            "tiers": tiers[currency]
        }
    })