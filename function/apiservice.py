from __main__ import app
import settings.define as define

from flask import request
from flask_caching import Cache
from settings.config import get_config
from settings.response import json_rsp, json_rsp_with_msg

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
            "disable_ysdk_guard": get_config()["Player"]["disable_ysdk_guard"],  
            "enable_announce_pic_popup": get_config()["Player"]["enable_announce_pic_popup"],  
            "protocol": get_config()["Player"]["protocol"],  
            "qr_enabled": get_config()["Player"]["qr_enabled"]
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
            "disable_mmt": get_config()["Login"]["disable_mmt"],                            # 禁用验证码
            "disable_regist": get_config()["Login"]["disable_regist"],                      # 禁止注册
            "enable_email_captcha": get_config()["Login"]["enable_email_captcha"],          # 启用邮箱验证
            "enable_ps_bind_account": get_config()["Login"]["enable_ps_bind_account"],      # 启用与PS平台相关联
            "game_key": request.args.get('game_key'),
            "guest": get_config()["Auth"]["enable_guest"],
            "server_guest": get_config()["Auth"]["enable_guest"],
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
            "modified": get_config()["Other"]["modified"],
            "protocol": {}
        }
    })

# 获取SDKCombo配置信息
@app.route('/combo/box/api/config/sdk/combo', methods=['GET'])
def combo_box_api_config_sdk_combo():
    return json_rsp_with_msg(define.RES_SUCCESS, "OK", {
        "data": {
            "disable_email_bind_skip": get_config()["Login"]["disable_email_bind_skip"], 
            "email_bind_remind": get_config()["Login"]["email_bind_remind"],  
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
                "enable": get_config()["Other"]["serviceworker"]         # 是否加载ServiceWorker进行分析
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
    
# 抓出来的我也不知道是什么 似乎是玩家登录信息   
@app.route('/hk4e_cn/combo/guard/api/ping', methods=['POST'])
@app.route('/hk4e_cn/combo/guard/api/ping2', methods=['POST'])
@app.route('/hk4e_global/combo/guard/api/ping',methods=['POST'])
@app.route('/hk4e_global/combo/guard/api/ping2',methods=['POST'])
def pingResponse():
   return json_rsp(define.RES_SUCCESS, {})