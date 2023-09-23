import sys
import os
import atexit
import logging
import time
import shutil
import codecs
import yaml
import pymysql
import settings.define as define
from datetime import datetime
from flask import Flask, request
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
import function.announcement
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

#======================mysql服务=====================#
def get_config():
    with open(define.CONFIG_FILE_PATH, encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config
# 检查连接
def check_mysql_connection():
    config = get_config()['Database']
    try:
        conn = pymysql.connect(
            host=config['host'],
            user=config['user'],
            port=config['port'],
            password=config['password'],
            charset='utf8mb4'
        )
        conn.close()
        return True
    except pymysql.Error:
        return False

# 检查连接后是否存在库
def check_database_exists():
    config = get_config()['Database']
    try:
        conn = pymysql.connect(
            host=config['host'],
            user=config['user'],
            port=config['port'],
            password=config['password'],
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        for db in databases:
            if db[0] == config['name']:
                return True
        cursor.close()
        conn.close()
        return False
    except pymysql.Error:
        return False
#======================log设置======================#
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

# 加载配置文件
def load_config():
    with open(define.CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

# 获取请求日志记录配置项
def get_request_logging_config():
    config = load_config()
    return config.get('Setting', {}).get('high_frequency_logs', False)

@app.before_request
def log_request_content():
    enable_request_logging = get_request_logging_config()
    if enable_request_logging:
        content = request.get_data(as_text=True)
        encoded_content = content.encode('utf-8')
        logging.info(f"[客户端上报]: {encoded_content}")

#======================Falsk(main)======================#
def start_flask_server(config):
    app.secret_key = config["Setting"]["secret_key"]
    app.debug = config["Setting"]["debug"]
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    mail_config = config.get('Mail', {})
    enable_mail = mail_config.get('ENABLE', True)
    if enable_mail:
        app.config.update(mail_config)
        mail = Mail(app)
        app.extensions['Mail'] = mail
    run_simple(
        config["Setting"]["listen"],
        config["Setting"]["port"],
        app,
        # use_reloader= config["Setting"]["reload"],    # 热重载1 按照config配置文件来设置
        # use_debugger= config["Setting"]["debug"],
        # threaded= config["Setting"]["threaded"]
        use_reloader=True,                              # 热重载2 快捷设置 方便debug
        use_debugger=False,
        threaded=True                                   # 多线程模式 默认开启
    )

def initialize_database():
    print(">> 正在初始化数据库结构(清空数据)...")
    if not check_mysql_connection():
        print("#======================Mysql连接失败！请检查服务配置======================#")
        sys.exit(1)
    database.init_db()
    print(">> 初始化结构完成")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise Exception("请提供命令行参数: serve 或 initdb")
    config = load_config()
    command = sys.argv[1]
    if command == "serve":
        if not check_mysql_connection():
            print("#======================Mysql连接失败！请检查服务配置======================#")
            sys.exit(1)
        if not check_database_exists():
            print("#=====================Mysql查询库失败！请检查服务配置=====================#")
            sys.exit(1)
        start_flask_server(config)
    elif command == "initdb":
        initialize_database()
    else:
        raise Exception("未知的操作！必须是以下命令: serve 或 initdb")