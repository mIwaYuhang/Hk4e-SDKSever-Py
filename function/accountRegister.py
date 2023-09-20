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

#=====================注册模块=====================#
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
