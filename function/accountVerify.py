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

#=====================校验模块=====================#
# 账号校验(t_sdk_config)
@app.route('/inner/account/verify', methods=['POST'])
def inner_account_verify():
    try:
        data = json.loads(request.data)
        cursor = get_db().cursor()
        token = cursor.execute("SELECT * FROM `combo_tokens` WHERE `token` = ? AND `uid` = ?",
                               (data["combo_token"], data["open_id"])).fetchone()
        if not token:
            return json_rsp(define.RES_SDK_VERIFY_FAIL, {})
        user = cursor.execute(
            "SELECT * FROM `accounts` WHERE `uid` = ?", (token["uid"], )).fetchone()
        if not user:
            print(
                f"Found valid combo_token={token['token']} for uid={token['uid']}, but no such account exists")
            return json_rsp(define.RES_SDK_VERIFY_FAIL, {})
        return json_rsp(define.RES_SDK_VERIFY_SUCC, {
            "data": {
                "guest": True if user["type"] == define.ACCOUNT_TYPE_GUEST else False,
                "account_type": user["type"],
                "account_uid": token["uid"],
                "ip_info": {
                    "country_code": get_country_for_ip(token["ip"]) or "ZZ"
                }
            }
        })
    except Exception as err:
        print(
            f"Unexpected {err=}, {type(err)=} while handling account verify event")
        return json_rsp(define.RES_SDK_VERIFY_FAIL, {})

# 账号风险验证
@app.route('/account/risky/api/check', methods=['POST'])
def account_risky_api_check():
    return json_rsp_with_msg(define.RES_SUCCESS, "OK", {
        "data": {
            "id": "none",
            "action": define.RISKY_ACTION_NONE,
            "geetest": None
        }
    })

# 验证account_id和combo_token
@app.route('/hk4e_cn/combo/granter/login/beforeVerify', methods=['POST'])
@app.route('/hk4e_global/combo/granter/login/beforeVerify', methods=['POST'])
def combo_granter_login_verify():
    return json_rsp_with_msg(define.RES_SUCCESS, "OK", {
        "data": {
            "is_guardian_required": False,      # 未满14周岁阻止登录
            "is_heartbeat_required": True,
            "is_realname_required": False       # 实名认证请求
        }
    })

# 二次登录校验
@app.route('/hk4e_cn/combo/granter/login/v2/login', methods=['POST'])
@app.route('/hk4e_global/combo/granter/login/v2/login', methods=['POST'])
def combo_granter_login_v2_login():
    try:
        cursor = get_db().cursor()
        data = json.loads(request.json["data"])
        if data["guest"]:
            guest = cursor.execute("SELECT * FROM `accounts_guests` WHERE `device` = ? AND `uid` = ?",
                                   (request.json["device"], data["uid"])).fetchone()
            if not guest:
                return json_rsp_with_msg(define.RES_LOGIN_FAILED, "游戏账号信息缓存错误", {})

            user = cursor.execute("SELECT * FROM `accounts` WHERE `uid` = ? AND `type` = ?",
                                  (data["uid"], define.ACCOUNT_TYPE_GUEST)).fetchone()
            if not user:
                print(
                    f"Found valid account_guest={guest['uid']} for device={guest['device']}, but no such account exists")
                return json_rsp_with_msg(define.RES_LOGIN_ERROR, "系统错误，请稍后再试", {})
        else:
            token = cursor.execute(
                "SELECT * FROM `accounts_tokens` WHERE `token` = ? AND `uid` = ?", (data["token"], data["uid"])).fetchone()
            if not token:
                return json_rsp_with_msg(define.RES_LOGIN_FAILED, "游戏账号信息缓存错误", {})

            user = cursor.execute("SELECT * FROM `accounts` WHERE `uid` = ? AND `type` = ?",
                                  (token["uid"], define.ACCOUNT_TYPE_NORMAL)).fetchone()
            if not user:
                print(
                    f"Found valid account_token={token['token']} for uid={token['uid']}, but no such account exists")
                return json_rsp_with_msg(define.RES_LOGIN_ERROR, "系统错误，请稍后再试", {})
        combo_token = ''.join(random.choice('0123456789abcdef')
                              for i in range(get_config()["security"]["token_length"]))
        cursor.execute(
            "INSERT OR REPLACE INTO `combo_tokens` (`uid`, `token`, `device`, `ip`, `epoch_generated`) VALUES (?, ?, ?, ?, ?)",
            (user["uid"], combo_token, request.json["device"],
             request_ip(request), int(epoch()))
        )
        return json_rsp_with_msg(define.RES_SUCCESS, "OK", {
            "data": {
                "account_type": user["type"],
                "data": json.dumps({"guest": True if data["guest"] else False}, separators=(',', ':')),
                "fatigue_remind": None,             # 国区专属 如果游戏时间过长，游戏内会显示提醒
                "heartbeat": False,                 # 国区专属 强制游戏发送心跳包 服务器可以强制游戏时间
                "open_id": data["uid"],
                "combo_token": combo_token
            }
        })
    except Exception as err:
        print(
            f"Unexpected {err=}, {type(err)=} while handling combo login event")
        return json_rsp_with_msg(define.RES_FAIL, "系统错误，请稍后再试", {})

# 游戏账号信息缓存校验
@app.route('/hk4e_cn/mdk/shield/api/verify', methods=['POST'])
@app.route('/hk4e_global/mdk/shield/api/verify', methods=['POST'])
def mdk_shield_api_verify():
    try:
        cursor = get_db().cursor()
        token = cursor.execute("SELECT * FROM `accounts_tokens` WHERE `token` = ? AND `uid` = ?",
                               (request.json["token"], request.json["uid"])).fetchone()
        if not token:
            return json_rsp_with_msg(define.RES_LOGIN_FAILED, "游戏账号信息缓存错误", {})
        if token["device"] != request.headers.get('x-rpc-device_id'):
            return json_rsp_with_msg(define.RES_LOGIN_FAILED, "游戏账号信息缓存错误", {})
        user = cursor.execute("SELECT * FROM `accounts` WHERE `uid` = ? AND `type` = ?",
                              (token["uid"], define.ACCOUNT_TYPE_NORMAL)).fetchone()
        if not user:
            print(
                f"Found valid account_token={token['token']} for uid={token['uid']}, but no such account exists")
            return json_rsp_with_msg(define.RES_LOGIN_ERROR, "系统错误，请稍后再试", {})
        return json_rsp_with_msg(define.RES_SUCCESS, "OK", {
            "data": {
                "account": {
                    "uid": user["uid"],
                    "name": mask_string(user["name"]),
                    "email": mask_email(user["email"]),
                    "is_email_verify": False,  
                    "token": token["token"],        # 重用token
                    "country": get_country_for_ip(request_ip(request)) or "ZZ",
                    "area_code": None               #如果使用GeoLite2-City，则可以填充
                }
            }
        })
    except Exception as err:
        print(
            f"Unexpected {err=}, {type(err)=} while handling shield verify event")
        return json_rsp_with_msg(define.RES_FAIL, "系统错误，请稍后再试", {})

