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

#=====================登录模块=====================#
# 玩家登录
@app.route('/hk4e_cn/mdk/shield/api/login', methods=['POST'])
@app.route('/hk4e_global/mdk/shield/api/login', methods=['POST'])
def mdk_shield_api_login():
    try:
        cursor = get_db().cursor()
        user = cursor.execute("SELECT * FROM `accounts` WHERE `name` = ? AND `type` = ?",
                              (request.json["account"], define.ACCOUNT_TYPE_NORMAL)).fetchone()
        if not user:
            return json_rsp_with_msg(define.RES_LOGIN_FAILED, "未找到用户名", {})
        if get_config()["auth"]["enable_password_verify"]:
            if request.json["is_crypto"] == True:
                password = decrypt_rsa_password(request.json["password"])
            else:
                password = request.json["password"]
            if not password_verify(password, user["password"]):
                return json_rsp_with_msg(define.RES_LOGIN_FAILED, "用户名或密码不正确", {})
        token = ''.join(random.choice(string.ascii_letters)
                        for i in range(get_config()["security"]["token_length"]))
        cursor.execute(
            "INSERT INTO `accounts_tokens` (`uid`, `token`, `device`, `ip`, `epoch_generated`) VALUES (?, ?, ?, ?, ?)",
            (user["uid"], token, request.headers.get(
                'x-rpc-device_id'), request_ip(request), int(epoch()))
        )
        return json_rsp_with_msg(define.RES_SUCCESS, "OK", {
            "data": {
                "account": {
                    "uid": user["uid"],
                    "name": mask_string(user["name"]),
                    "email": mask_email(user["email"]),
                    "is_email_verify": False,  
                    "token": token,
                    "country": get_country_for_ip(request_ip(request)) or "ZZ",
                    "area_code": None
                },
                "device_grant_required": False,                # 强制新设备的邮件授权
                "realname_operation": None,
                "realperson_required": False,
                "safe_mobile_required": False  
            }
        })
    except Exception as err:
        print(
            f"Unexpected {err=}, {type(err)=} while handling shield login event")
        return json_rsp_with_msg(define.RES_FAIL, "系统错误，请稍后再试", {})

# 快速游戏
@app.route('/hk4e_cn/mdk/guest/guest/login', methods=['POST'])
@app.route('/hk4e_cn/mdk/guest/guest/v2/login', methods=['POST'])
@app.route('/hk4e_global/mdk/guest/guest/login', methods=['POST'])
@app.route('/hk4e_global/mdk/guest/guest/v2/login', methods=['POST'])
def mdk_guest_login():
    if not get_config()["auth"]["enable_server_guest"]:
        return json_rsp_with_msg(define.RES_LOGIN_CANCEL, "访客模式已关闭", {})
    try:
        cursor = get_db().cursor()
        guest = cursor.execute(
            "SELECT * FROM `accounts_guests` WHERE `device` = ?", (request.json["device"], )).fetchone()
        if not guest:
            cursor.execute("INSERT INTO `accounts` (`type`, `epoch_created`) VALUES (?, ?)",
                           (define.ACCOUNT_TYPE_GUEST, int(epoch())))
            user = {"uid": cursor.lastrowid, "type": define.ACCOUNT_TYPE_GUEST}
            cursor.execute("INSERT INTO `accounts_guests` (`uid`, `device`) VALUES (?, ?)",
                           (user["uid"], request.json["device"]))
        else:
            user = cursor.execute("SELECT * FROM `accounts` WHERE `uid` = ? AND `type` = ?",
                                  (guest["uid"], define.ACCOUNT_TYPE_GUEST)).fetchone()
            if not user:
                print(
                    f"Found valid account_guest={guest['uid']} for device={guest['device']}, but no such account exists")
                return json_rsp_with_msg(define.RES_LOGIN_ERROR, "系统错误，请稍后再试", {})                  # 客户绑定存在的帐户不在数据库中时
        return json_rsp_with_msg(define.RES_SUCCESS, "OK", {
            "data": {
                "account_type": user["type"],
                "guest_id": user["uid"]
            }
        })
    except Exception as err:
        print(
            f"Unexpected {err=}, {type(err)=} while handling guest login event")
        return json_rsp_with_msg(define.RES_FAIL, "系统错误，请稍后再试", {})