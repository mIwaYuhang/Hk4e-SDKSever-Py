import sys
import os
import atexit
import logging
import time
import shutil
from datetime import datetime
from flask import Flask
from flask_mail import Mail
from werkzeug.serving import run_simple
from werkzeug.middleware.proxy_fix import ProxyFix
app = Flask(__name__)
from settings.config import load_config
import settings.database as database
import function.accountregister
import function.accountrecover
import function.loginservice
import function.dispatch
import function.rechargeservice
import function.apiservice
import function.accountverify
import function.gachaservice
import function.otherservice

#=====================log设置=====================#
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'sdkserver-running.log')
logging.basicConfig(filename=log_file, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

logger = logging.getLogger()
logger.addHandler(console_handler)

def rename_log_file():
    logger.removeHandler(console_handler)
    logging.shutdown()
    console_handler.close()
    time.sleep(1)
    now = datetime.now()
    new_filename = now.strftime("sdkserver-%Y-%m-%d %H-%M-%S.0000")
    new_log_file = os.path.join(log_dir, new_filename)
    shutil.move(log_file, new_log_file)
atexit.register(rename_log_file)

#=====================Falsk(main)=====================#
def start_flask_server(config):
    app.secret_key = config["app"]["secret_key"]
    app.debug = config["app"]["debug"]
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    mail_config = config.get('mail', {})
    enable_mail = mail_config.get('open', True)
    if enable_mail:
        app.config.update(mail_config)
        mail = Mail(app)
        app.extensions['mail'] = mail
    run_simple(
        config["app"]["listen"],
        config["app"]["port"],
        app,
        # use_reloader= config["app"]["reload"], # 热重载1 按照config配置文件来设置
        # use_debugger= config["app"]["debug"],
        # threaded= config["app"]["threaded"]
        use_reloader= True,                     # 热重载2 快捷设置 方便debug
        use_debugger= False,
        threaded= True                           # 多线程模式 默认开启
    )

def initialize_database():
    print(">> 正在初始化数据库结构(清空数据)...")
    database.init_db()
    print(">> 完成!")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise Exception("请提供命令行参数: serve, initdb")
    config = load_config()
    command = sys.argv[1]
    if command == "serve":
        print(">> Flask服务已启动...")
        start_flask_server(config)
    elif command == "clear":
        initialize_database()
    else:
        raise Exception("未知的操作，必须是以下命令: serve, clear")
