from __main__ import app
import json
import random
import settings.repositories as repositories

from flask import request
from time import time as epoch
from flask_caching import Cache
from settings.database import get_db
from settings.loadconfig import get_config
from settings.response import json_rsp, json_rsp_with_msg
from settings.library import request_ip, get_country_for_ip, mask_string, mask_email

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
        token_query = "SELECT * FROM `combo_tokens` WHERE `token` = %s AND `uid` = %s"
        cursor.execute(token_query, (data["combo_token"], data["open_id"]))
        token = cursor.fetchone()
        if not token:
            return json_rsp(repositories.RES_SDK_VERIFY_FAIL, {})
        user_query = "SELECT * FROM `accounts` WHERE `uid` = %s"
        cursor.execute(user_query, (token["uid"],))
        user = cursor.fetchone()
        if not user:
            print(f"Found valid combo_token={token['token']} for uid={token['uid']}, but no such account exists")
            return json_rsp(repositories.RES_SDK_VERIFY_FAIL, {})
        return json_rsp(repositories.RES_SDK_VERIFY_SUCC, {
            "data": {
                "guest": True if user["type"] == repositories.ACCOUNT_TYPE_GUEST else False,
                "account_type": user["type"],
                "account_uid": str(token["uid"]),
                "ip_info": {
                    "country_code": get_country_for_ip(token["ip"]) or "CN"
                }
            }
        })
    except Exception as err:
        print(f"处理账号校验事件时出现意外错误{err=}, {type(err)=}")
        return json_rsp(repositories.RES_SDK_VERIFY_FAIL, {})

# 账号风险验证
@app.route('/account/risky/api/check', methods=['POST'])
def account_risky_api_check():
    return json_rsp_with_msg(repositories.RES_SUCCESS, "OK", {
        "data": {
            "id": "none",
            "action": repositories.RISKY_ACTION_NONE,
            "geetest": None
        }
    })

# 验证account_id和combo_token
@app.route('/hk4e_cn/combo/granter/login/beforeVerify', methods=['POST'])
@app.route('/hk4e_global/combo/granter/login/beforeVerify', methods=['POST'])
def combo_granter_login_verify():
    return json_rsp_with_msg(repositories.RES_SUCCESS, "OK", {
        "data": {
            "is_guardian_required": get_config()["Player"]["guardian_required"],      # 未满14周岁阻止登录
            "is_heartbeat_required": get_config()["Player"]["heartbeat_required"],
            "is_realname_required": get_config()["Player"]["realname_required"]       # 实名认证请求
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
            guest_query = "SELECT * FROM `accounts_guests` WHERE `device` = %s AND `uid` = %s"
            cursor.execute(guest_query, (request.json["device"], data["uid"]))
            guest = cursor.fetchone()
            if not guest:
                return json_rsp_with_msg(repositories.RES_LOGIN_FAILED, "游戏账号信息缓存错误", {})
            user_query = "SELECT * FROM `accounts` WHERE `uid` = %s AND `type` = %s"
            cursor.execute(user_query, (data["uid"], repositories.ACCOUNT_TYPE_GUEST))
            user = cursor.fetchone()
            if not user:
                print(f"Found valid account_guest={guest['uid']} for device={guest['device']}, but no such account exists")
                return json_rsp_with_msg(repositories.RES_LOGIN_ERROR, "系统错误，请稍后再试", {})
        else:
            token_query = "SELECT * FROM `accounts_tokens` WHERE `token` = %s AND `uid` = %s"
            cursor.execute(token_query, (data["token"], data["uid"]))
            token = cursor.fetchone()
            if not token:
                return json_rsp_with_msg(repositories.RES_LOGIN_FAILED, "游戏账号信息缓存错误", {})
            user_query = "SELECT * FROM `accounts` WHERE `uid` = %s AND `type` = %s"
            cursor.execute(user_query, (token["uid"], repositories.ACCOUNT_TYPE_NORMAL))
            user = cursor.fetchone()
            if not user:
                print(f"Found valid account_token={token['token']} for uid={token['uid']}, but no such account exists")
                return json_rsp_with_msg(repositories.RES_LOGIN_ERROR, "系统错误，请稍后再试", {})
        combo_token = ''.join(random.choices('0123456789abcdef', k=get_config()["Security"]["token_length"]))
        device = request.json["device"]
        ip = request_ip(request)
        epoch_generated = int(epoch())
        combo_token_query = "INSERT INTO `combo_tokens` (`uid`, `token`, `device`, `ip`, `epoch_generated`) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE `token` = VALUES(`token`), `device` = VALUES(`device`), `ip` = VALUES(`ip`), `epoch_generated` = VALUES(`epoch_generated`)"
        cursor.execute(combo_token_query, (user["uid"], combo_token, device, ip, epoch_generated))
        return json_rsp_with_msg(repositories.RES_SUCCESS, "OK", {
            "data": {
                "combo_id": 0,
                "account_type": user["type"],
                "data": json.dumps({"guest": True if data["guest"] else False}, separators=(',', ':')),
                "fatigue_remind": {
                    "nickname": "旅行者",
                    "reset_point": 14400,
                    "durations": [180, 240, 300]
                },
                "heartbeat": get_config()["Player"]["heartbeat_required"],
                "open_id": str(data["uid"]),
                "combo_token": combo_token
            }
        })
    except Exception as err:
        print(f"处理 combo 登录事件时出现意外错误 {err=}，{type(err)=}")
        return json_rsp_with_msg(repositories.RES_FAIL, "系统错误，请稍后再试", {})

# 游戏账号信息缓存校验
@app.route('/hk4e_cn/mdk/shield/api/verify', methods=['POST'])
@app.route('/hk4e_global/mdk/shield/api/verify', methods=['POST'])
def mdk_shield_api_verify():
    try:
        cursor = get_db().cursor()
        token_query = "SELECT * FROM `accounts_tokens` WHERE `token` = %s AND `uid` = %s"
        cursor.execute(token_query, (request.json["token"], request.json["uid"]))
        token = cursor.fetchone()
        if not token:
            return json_rsp_with_msg(repositories.RES_LOGIN_FAILED, "游戏账号信息缓存错误", {})
        if token["device"] != request.headers.get('x-rpc-device_id'):
            return json_rsp_with_msg(repositories.RES_LOGIN_FAILED, "登录态失效，请重新登录", {})
        user_query = "SELECT * FROM `accounts` WHERE `uid` = %s AND `type` = %s"
        cursor.execute(user_query, (token["uid"], repositories.ACCOUNT_TYPE_NORMAL))
        user = cursor.fetchone()
        if not user:
            print(f"Found valid account_token={token['token']} for uid={token['uid']}, but no such account exists")
            return json_rsp_with_msg(repositories.RES_LOGIN_ERROR, "系统错误，请稍后再试", {})
        return json_rsp_with_msg(repositories.RES_SUCCESS, "OK", {
            "data": {
                "account": {
                    "uid": str(user["uid"]),
                    "name": mask_string(user["name"]),
                    "email": mask_email(user["email"]),
                    "is_email_verify": get_config()["Login"]["email_verify"],
                    "token": token["token"],
                    "country": get_country_for_ip(request_ip(request)) or "CN",
                    "area_code": None
                }
            }
        })
    except Exception as err:
        print(f"处理 MDK Shield API 验证时出现意外错误 {err=}，{type(err)=}")
        return json_rsp_with_msg(repositories.RES_FAIL, "系统错误，请稍后再试", {})

