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

#=====================SDKServer=====================#
# 首页
@app.route('/')
@app.route('/sandbox/index.html', methods=['GET'])
def account_index():
    return render_template("account/index.tmpl")

# 检查SDK配置(https://testing-abtest-api-data-sg.mihoyo.com)
@app.route('/data_abtest_api/config/experiment/list', methods=['GET', 'POST'])
def abtest_config_experiment_list():
    return json_rsp_with_msg(define.RES_SUCCESS, "OK", {
        "data": []
    })

#=====================状态收集=====================#
# log收集
@app.route('/log', methods=['POST'])
@app.route('/log/sdk/upload', methods=['POST'])
@app.route('/crash/dataUpload', methods=['POST'])
@app.route('/client/event/dataUpload', methods = ['POST'])
@app.route('/sdk/dataUpload', methods=['POST'])
@app.route('/common/h5log/log/batch', methods=['POST'])
def sdk_log():
    return json_rsp(define.RES_SUCCESS, {})

#=====================mi18n=====================#
@app.route('/admin/mi18n/plat_cn/m2020030410/m2020030410-version.json', methods=['GET'])
@app.route('/admin/mi18n/plat_oversea/m2020030410/m2020030410-version.json', methods=['GET'])
def mi18n_version():
    return json_rsp(define.RES_SUCCESS, {"version": 51})
@app.route('/admin/mi18n/plat_cn/m2020030410/m2020030410-<language>.json', methods=['GET'])
@app.route('/admin/mi18n/plat_oversea/m2020030410/m2020030410-<language>.json', methods=['GET'])
def mi18n_serve(language):
    return send_from_directory(define.MI18N_PATH, f"{language}.json")
