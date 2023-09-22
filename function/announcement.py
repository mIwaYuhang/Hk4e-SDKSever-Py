from __main__ import app
import os
import settings.define as define

from flask import render_template, send_file
from flask_caching import Cache
from settings.config import get_config
from settings.response import json_rsp_with_msg

cache = Cache(app, config={'CACHE_TYPE': 'simple'})
@app.context_processor
def inject_config():
    config = get_config()
    return {'config': config}

#=====================公告模块=====================#
# 公告功能
@app.route('/common/hk4e_cn/announcement/api/getAlertAnn',methods = ['GET'])
@app.route('/common/hk4e_global/announcement/api/getAlertAnn',methods = ['GET'])
def get_alertann():
    return json_rsp_with_msg(define.RES_SUCCESS, "OK", {
        "data": {
            "alert": get_config()["Announce"]["alert"],
            "alert_id": 0,
            "remind": get_config()["Announce"]["remind"],
            "extra_remind": get_config()["Announce"]["extra_remind"]
        }
    })

# 获取公告
@app.route('/common/hk4e_cn/announcement/api/getAlertPic', methods=['GET'])
@app.route('/common/hk4e_cn/announcement/api/getAnnList', methods=['GET'])
@app.route('/common/hk4e_global/announcement/api/getAlertPic', methods=['GET'])
@app.route('/common/hk4e_global/announcement/api/getAnnList', methods=['GET'])
def get_alertPic():
    file_path = define.ANNOUNCE_PATH
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return "Not found"

@app.route('/common/hk4e_cn/announcement/api/getAnnContent', methods=['GET'])
@app.route('/common/hk4e_global/announcement/api/getAnnContent', methods=['GET'])
def ann_content():
    file_path = define.ANNOUNCE_CONTENT_PATH
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return "Not found"

# 公告模块
@app.route('/hk4e/announcement/index.html', methods=['GET'])
def handle_announcement():
    return render_template("announce/announcement.tmpl")

# 资源文件
@app.route('/hk4e/announcement/2_2e4d2779ad3d19e6406f.js',methods=['GET'])
def get_js():
    file_path = define.ANNOUNCE_JS_PATH
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return "Not found"
@app.route('/hk4e/announcement/2_cb04d2d72d7555e2ab83.css',methods=['GET'])
def get_css():
    file_path = define.ANNOUNCE_CSS_PATH
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return "Not found"
@app.route('/favicon.ico',methods=['GET'])
def get_favicon():
    file_path = define.ANNOUNCE_FAVICON_PATH
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return "Not found"
@app.route('/dora/lib/vue/2.6.11/vue.min.js',methods=['GET'])
def get_vue_min():
    file_path = define.ANNOUNCE_VUEMIN_PATH
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return "Not found"
@app.route('/dora/biz/mihoyo-analysis/v2/main.js',methods=['GET'])
def get_mainjs():
    file_path = define.ANNOUNCE_MAINJS_PATH
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return "Not found"
@app.route('/dora/biz/mihoyo-h5log/v1.0/main.js',methods=['GET'])
def get_mainh5js():
    file_path = define.ANNOUNCE_MAINH5JS_PATH
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return "Not found"
@app.route('/dora/lib/firebase-performance/8.2.7/firebase-performance-standalone-cn.js',methods=['GET'])
@app.route('/dora/lib/firebase-performance/8.2.7/firebase-performance-standalone.js',methods=['GET'])
def get_fprjs():
    file_path = define.ANNOUNCE_FPTJS_PATH
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return "Not found"
