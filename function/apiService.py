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

#=====================Api功能=====================#
# Api-Config(https://sandbox-sdk-os.hoyoverse.com)
@app.route('/hk4e_cn/combo/granter/api/getConfig', methods=['GET'])
@app.route('/hk4e_global/combo/granter/api/getConfig', methods=['GET'])
def combo_granter_api_config():
    return json_rsp_with_msg(define.RES_SUCCESS, "OK", {
        "data": {
            "disable_ysdk_guard": True,  
            "enable_announce_pic_popup": False,  
            "protocol": False,  
            "qr_enabled": False
        }
    })

# 登录相关
@app.route('/hk4e_cn/mdk/shield/api/loadConfig', methods=['GET', 'POST'])
@app.route('/hk4e_global/mdk/shield/api/loadConfig', methods=['GET', 'POST'])
def mdk_shield_api_loadConfig():
    client = request.args.get('client', '')  # 提供默认值为空字符串
    if client.isdigit():
        client = define.PLATFORM_TYPE[int(client)]
    return json_rsp_with_msg(define.RES_SUCCESS, "OK", {
        "data": {
            "client": client,
            "disable_mmt": True,                    # 禁用验证码
            "disable_regist": False,                # 禁止注册
            "enable_email_captcha": False,          # 启用邮箱验证
            "enable_ps_bind_account": False,        # 启用与PS平台相关联
            "game_key": request.args.get('game_key'),
            "guest": get_config()["auth"]["enable_server_guest"],
            "server_guest": get_config()["auth"]["enable_server_guest"],
            "identity": "I_IDENTITY",
            "name": "原神海外",
            "scene": define.SCENE_USER,
            "thirdparty": []
        }
    })

# 获取协议信息
@app.route('/hk4e_cn/mdk/agreement/api/getAgreementInfos', methods=['GET'])
@app.route('/hk4e_global/mdk/agreement/api/getAgreementInfos', methods=['GET'])
def mdk_agreement_api_get():
    return json_rsp_with_msg(define.RES_SUCCESS, "OK", {
        "data": {
            "marketing_agreements": []
        }
    })

# 协议比较(https://sandbox-sdk-os.hoyoverse.com)
@app.route('/hk4e_cn/combo/granter/api/compareProtocolVersion', methods=['POST'])
@app.route('/hk4e_global/combo/granter/api/compareProtocolVersion', methods=['POST'])
def combo_granter_api_protocol():
    return json_rsp_with_msg(define.RES_SUCCESS, "OK", {
        "data": {
            "modified": False,
            "protocol": {}
        }
    })

# 获取SDKCombo配置信息
@app.route('/combo/box/api/config/sdk/combo', methods=['GET'])
def combo_box_api_config_sdk_combo():
    return json_rsp_with_msg(define.RES_SUCCESS, "OK", {
        "data": {
            "disable_email_bind_skip": False,  
            "email_bind_remind": False  
        }
    })

# 全局红点列
@app.route('/hk4e_cn/combo/red_dot/list', methods=['POST'])
@app.route('/hk4e_global/combo/red_dot/list', methods=['POST'])
def combo_red_dot_list():
    return json_rsp_with_msg(define.RES_SUCCESS, "OK", {
        "data": {
            "infos": []                 # 基于玩家级别和uid的动态设置
        }
    })

# 预加载
@app.route('/combo/box/api/config/sw/precache', methods=['GET'])
def combo_box_api_config_sw_precache():
    return json_rsp_with_msg(define.RES_SUCCESS, "OK", {
        "data": {
            "vals": {
                "enable": False         # 是否加载ServiceWorker进行分析
            }
        }
    })

# 指纹采集？
@app.route('/device-fp/api/getExtList', methods=['GET'])
def device_fp_get_ext_list():
    return json_rsp_with_msg(define.RES_SUCCESS, "OK", {
        "data": {
            "code": "200",
            "ext_list": [],             # 列表为空表示禁用客户端指纹识别
            "pkg_list": None
        }
    })
    
# 抓出来的我也不知道是什么(国内沙箱) 似乎是玩家登录信息   
@app.route('/hk4e_cn/combo/guard/api/ping', methods=['POST'])
def pingResponse():
   return json_rsp(define.RES_SUCCESS, {})