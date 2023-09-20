from flask import Flask
from flask_mail import Mail
from flask_caching import Cache
from werkzeug.middleware.proxy_fix import ProxyFix
app = Flask(__name__)
import sys

from settings.config import load_config
import settings.database as database
import routes

if __name__ == '__main__':
   config = load_config()
   
   app.secret_key = config["app"]["secret_key"]
   app.debug = config["app"]["debug"]
   app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

   if sys.argv[1] == "serve":
      print(">> Flask服务已启动...")
      mail_config = config.get('mail', {})
      enable_mail = mail_config.get('open', False)

      if enable_mail:
         app.config.update(mail_config)
         mail = Mail(app)
      app.run(config["app"]["listen"], config["app"]["port"])
   elif sys.argv[1] == "initdb":
      print(">> 正在初始化数据库结构...")
      database.init_db()
      print(">> 完成!")
   else:
      raise Exception("未知的操作，必须是以下命令: serve, initdb")
