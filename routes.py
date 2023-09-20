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

#=====================用户注册模块=====================#
# 游戏账号注册
@app.route('/account/register', methods=['GET', 'POST'])
@app.route('/mihoyo/common/accountSystemSandboxFE/index.html', methods=['GET', 'POST'])         # 国内沙箱 注册和找回URL是同一个
def account_register():
    cursor = get_db().cursor()
    cached_data = cache.get(request.form.get('email'))

    if request.method == 'POST':
        user = cursor.execute("SELECT * FROM `accounts` WHERE `name` = ?",
                              (request.form.get('username'), )).fetchone()
        if user:
            flash('您准备注册的用户名已被使用', 'error')
        elif not re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', request.form.get('email')):
            flash('邮箱格式不正确', 'error')
        elif request.form.get('code') != cached_data and get_config()['mail']['open']:
            flash('验证码错误', 'error')
        elif request.form.get('password') != request.form.get('passwordv2'):
            flash('两次输入的密码不一致', 'error')
        elif len(request.form.get('password')) < get_config()["security"]["min_password_len"]:
            flash(
                f"密码长度不能小于 {get_config()['security']['min_password_len']} 字节", 'error')
        else:
            cursor.execute(
                "INSERT INTO `accounts` (`name`, `email`, `password`, `type`, `epoch_created`) VALUES (?, ?, ?, ?, ?)",
                (request.form.get('username'), request.form.get('email'), password_hash(
                    request.form.get('password')), define.ACCOUNT_TYPE_NORMAL, int(epoch()))
            )
            flash('游戏账号注册成功，请返回登录', 'success')
            cache.delete(request.form.get('email'))
    return render_template("account/register.tmpl")

# 邮件验证码 用于注册
@app.route('/account/send_email', methods=['POST'])
def send_email():
    email = request.form.get('email')
    email_pattern = '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    if not re.match(email_pattern, email):
        return json_rsp_with_msg(define.RES_FAIL,"邮箱格式不正确",{})
    cursor = get_db().cursor()
    user = cursor.execute("SELECT * FROM `accounts` WHERE `email` = ?",
                              (email, )).fetchone()
    if user:
        return json_rsp_with_msg(define.RES_FAIL,"邮箱已被占用",{})
    verification_code = ''.join(random.choices(string.digits, k=4))
    mail = current_app.extensions['mail']
    msg = Message(f"{get_config()['web']['title']}注册验证码", recipients=[email])
    msg.body = f"你的注册验证码是：{verification_code}，验证码5分钟内有效"
    try:
        mail.send(msg)
    except:
        return json_rsp_with_msg(define.RES_FAIL,"未知异常，请联系管理员",{})
    cache.set(email, verification_code, timeout=60*5)
    return json_rsp_with_msg(define.RES_SUCCESS,"验证码发送成功，请查收邮箱。",{})

# 找回密码(功能不可用)
@app.route('/account/recover', methods=['GET', 'POST'])
def account_recover():
    if request.method == 'POST':
        flash('服务不可用', 'error')
    return render_template("account/recover.tmpl")

#=====================登录模块=====================#
# 登录配置
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

# 玩家登录校验
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

#=====================游戏内=====================#
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

#=====================mi18n=====================#
@app.route('/admin/mi18n/plat_cn/m2020030410/m2020030410-version.json', methods=['GET'])
@app.route('/admin/mi18n/plat_oversea/m2020030410/m2020030410-version.json', methods=['GET'])
def mi18n_version():
    return json_rsp(define.RES_SUCCESS, {"version": 51})
@app.route('/admin/mi18n/plat_cn/m2020030410/m2020030410-<language>.json', methods=['GET'])
@app.route('/admin/mi18n/plat_oversea/m2020030410/m2020030410-<language>.json', methods=['GET'])
def mi18n_serve(language):
    return send_from_directory(define.MI18N_PATH, f"{language}.json")

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

#=====================未开发的功能=====================#
# 新设备邮箱验证(路由指向/hk4e_global/mdk/shield/api/login)
@app.route("/account/device/api/preGrantByTicket",methods=['POST'])
def newEquipmentMailVerify():
    return

# 实名认证
@app.route("/hk4e_cn/mdk/shield/api/actionTicket",methods=['POST'])
def relNameVerify():
    return

