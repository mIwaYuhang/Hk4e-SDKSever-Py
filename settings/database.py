from __main__ import app
import sys
import yaml
import pymysql
import settings.database as database
import settings.repositories as repositories

from settings.checkstatus import check_mysql_connection
from flask import g

#=====================数据库创建=====================#
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_config():
    with open(repositories.CONFIG_FILE_PATH, encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        config = get_config()['Database']
        db = g._database = pymysql.connect(
            host=config['host'],
            user=config['user'],
            port=config['port'],
            password=config['password'],
            database=config['name'],
            cursorclass=pymysql.cursors.DictCursor
        )
    return db

def init_db(auto_create = get_config()['Database']['autocreate']):
    config = get_config()['Database']
    conn = pymysql.connect(
        host=config['host'],
        user=config['user'],
        port=config['port'],
        password=config['password'],
        charset='utf8mb4'
    )
    cursor = conn.cursor()
    if auto_create:
        cursor.execute("CREATE DATABASE IF NOT EXISTS `{}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci".format(config['name']))
    cursor.execute("USE `{}`".format(config['name']))
    cursor.execute("DROP TABLE IF EXISTS `accounts`")
    cursor.execute("DROP TABLE IF EXISTS `accounts_tokens`")
    cursor.execute("DROP TABLE IF EXISTS `accounts_guests`")
    cursor.execute("DROP TABLE IF EXISTS `accounts_events`")
    cursor.execute("DROP TABLE IF EXISTS `accounts_thirdparty`")
    cursor.execute("DROP TABLE IF EXISTS `thirdparty_tokens`")
    cursor.execute("DROP TABLE IF EXISTS `combo_tokens`")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS `accounts` (
                     `uid` INT AUTO_INCREMENT COMMENT '玩家UID',
                     `name` VARCHAR(255) UNIQUE COMMENT '用户名',
                     `mobile` VARCHAR(255) UNIQUE COMMENT '手机号',
                     `email` VARCHAR(255) UNIQUE COMMENT '电子邮件',
                     `password` VARCHAR(255) COMMENT '哈希密码',
                     `type` INT NOT NULL COMMENT '类型',
                     `epoch_created` INT NOT NULL COMMENT '时间戳',
                     PRIMARY KEY(`uid`,`name`,`mobile`,`email`)
                  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                  COMMENT='玩家账号信息表'
    """)
    cursor.execute("""CREATE TABLE IF NOT EXISTS `accounts_tokens` (
                     `uid` INT NOT NULL COMMENT '玩家UID',
                     `token` VARCHAR(255) NOT NULL COMMENT '登录Token',
                     `device` VARCHAR(255) NOT NULL COMMENT '设备ID',
                     `ip` VARCHAR(255) NOT NULL COMMENT '登录IP',
                     `epoch_generated` INT NOT NULL COMMENT '时间戳',
                     PRIMARY KEY(`uid`,`token`)
                  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                  COMMENT='账号登录token'
    """)
    cursor.execute("""CREATE TABLE IF NOT EXISTS `accounts_guests` (
                     `uid` INT NOT NULL COMMENT '玩家UID',
                     `device` VARCHAR(255) NOT NULL COMMENT '设备ID',
                     PRIMARY KEY(`uid`,`device`)
                  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                  COMMENT='游客登录信息表'
    """)
    cursor.execute("""CREATE TABLE IF NOT EXISTS `accounts_events` (
                     `uid` INT NOT NULL COMMENT '玩家UID',
                     `method` VARCHAR(255) NOT NULL COMMENT '登录方式',
                     `account_tpye` INT NOT NULL COMMENT '账号类型',
                     `account_id` INT NOT NULL COMMENT '账号ID',
                     `platform` INT NOT NULL COMMENT '平台',
                     `region` VARCHAR(255) NOT NULL COMMENT '区服信息',
                     `biz_game` VARCHAR(255) NOT NULL,
                     `epoch_created` INT NOT NULL COMMENT '时间戳',
                     PRIMARY KEY(`epoch_created`)
                  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                  COMMENT='账号活动记录表 由GameServer控制'
    """)
    cursor.execute("""CREATE TABLE IF NOT EXISTS `accounts_thirdparty` (
                     `uid` INT NOT NULL COMMENT '玩家UID',
                     `type` INT NOT NULL COMMENT '类型',
                     `external_name` VARCHAR(255) NOT NULL COMMENT '标识名称',
                     `external_id` INT NOT NULL COMMENT '标识ID',
                     PRIMARY KEY(`uid`,`type`)
                  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                  COMMENT='第三方账号登录信息表'
    """)
    cursor.execute("""CREATE TABLE IF NOT EXISTS `thirdparty_tokens` (
                     `uid` INT NOT NULL COMMENT '玩家UID',
                     `type` INT NOT NULL COMMENT '类型',
                     `token` VARCHAR(255) NOT NULL COMMENT '登录Token'
                  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                  COMMENT='第三方账号登录token'
    """)
    cursor.execute("""CREATE TABLE IF NOT EXISTS `combo_tokens` (
                     `uid` INT NOT NULL COMMENT '玩家UID',
                     `token` VARCHAR(255) NOT NULL COMMENT '登录Token',
                     `device` VARCHAR(255) NOT NULL COMMENT '设备ID',
                     `ip` VARCHAR(255) NOT NULL COMMENT '登录IP',
                     `epoch_generated` INT NOT NULL COMMENT '时间戳',
                     PRIMARY KEY(`uid`)
                  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                  COMMENT='设备信息token'
    """)

    conn.commit()
    conn.close()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.commit()
        db.close()

# 重置数据库
def initialize_database():
    print(">> 正在初始化数据库结构(清空数据)...")
    if not check_mysql_connection():
        print("#======================Mysql连接失败！请检查服务配置======================#")
        sys.exit(1)
    database.init_db()
    print(">> 初始化数据库完成")