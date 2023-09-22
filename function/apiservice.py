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

def json_rsp(code, message, data=None):
    response = {
        "code": code,
        "message": message
    }
    if data is not None:
        response["data"] = data
    return response

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
            "id": 6,
            "game_key": request.args.get('game_key'),
            "client": client,
            "identity": "I_IDENTITY",
            "guest": get_config()["Auth"]["enable_guest"],
            "ignore_versions": "",
            "scene": define.SCENE_ACCOUNT,
            "name": "原神",
            "disable_regist": get_config()["Login"]["disable_regist"],                     
            "enable_email_captcha": get_config()["Login"]["enable_email_captcha"],          
            "thirdparty": ["tp"],
            "disable_mmt": get_config()["Login"]["disable_mmt"],                            
            "server_guest": get_config()["Auth"]["enable_guest"],
            "thirdparty_ignore": {},
            "enable_ps_bind_account": get_config()["Login"]["enable_ps_bind_account"],
		    "thirdparty_login_configs": {},
		    "initialize_firebase": get_config()["Login"]["initialize_firebase"],
		    "bbs_auth_login": get_config()["Login"]["bbs_auth_login"],
		    "bbs_auth_login_ignore": [],
		    "fetch_instance_id": get_config()["Login"]["fetch_instance_id"],
		    "enable_flash_login": get_config()["Login"]["enable_flash_login"]
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

# 红点配置 一般infos为空 特别写的
@app.route('/hk4e_cn/combo/red_dot/list', methods=['POST'])
@app.route('/hk4e_global/combo/red_dot/list', methods=['POST'])
def red_dot():
    return json_rsp(define.RES_SUCCESS, "ok", {
        "infos": []
    })
"""
def red_dot():
    return json_rsp(define.RES_SUCCESS, "ok", {
        "infos": [
            {
                "red_point_type": 2201,
                "content_id": 184,
                "display": get_config()["Reddot"]["display"]
            }
        ]
    })
"""

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

# 问卷调查
@app.route('/device-fp/api/getExtList', methods=['GET'])
def device_fp_get_ext_list():
    return json_rsp_with_msg(define.RES_SUCCESS, "OK", {
	"data": {
		"code": 200,
		"msg": "ok",
		"ext_list": ["userAgent", "browserScreenSize", "maxTouchPoints", "isTouchSupported", "browserLanguage", "browserPlat", "browserTimeZone", "webGlRender", "webGlVendor", "numOfPlugins", "listOfPlugins", "screenRatio", "deviceMemory", "hardwareConcurrency", "cpuClass", "ifNotTrack", "ifAdBlock", "hasLiedLanguage", "hasLiedResolution", "hasLiedOs", "hasLiedBrowser"],
		"pkg_list": [],
		"pkg_str": ""
	}
    })
    
# 抓出来的我也不知道是什么 似乎是玩家登录信息   
@app.route('/hk4e_cn/combo/guard/api/ping', methods=['POST'])
@app.route('/hk4e_cn/combo/guard/api/ping2', methods=['POST'])
@app.route('/hk4e_global/combo/guard/api/ping',methods=['POST'])
@app.route('/hk4e_global/combo/guard/api/ping2',methods=['POST'])
def pingResponse():
   return json_rsp(define.RES_SUCCESS, {})

# 消费提醒
@app.route('/common/hk4e_cn/announcement/api/consumeRemind',methods=['GET'])
@app.route('/common/hk4e_global/announcement/api/consumeRemind',methods=['GET'])
def consume_remind():
    return json_rsp_with_msg(define.RES_SUCCESS, "OK", {
        "data": []
    })