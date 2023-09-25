import yaml
import pymysql
import settings.repositories as repositories

def get_config():
    with open(repositories.CONFIG_FILE_PATH, encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config

#======================mysql检查=====================#
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

#=====================Config检查完整性=====================#
def check_config():
    try:
        with open(repositories.CONFIG_FILE_PATH, 'r',encoding='utf-8') as file:
            config = yaml.safe_load(file)
        required_settings = {
            'Setting': ['listen', 'port', 'reload', 'debug', 'threaded', 'high_frequency_logs', 'secret_key'],
            'Database': ['host', 'user', 'port', 'autocreate', 'name', 'password'],
            'Login': ['disable_mmt', 'disable_regist', 'disable_email_bind_skip', 'enable_email_captcha', 'enable_ps_bind_account', 'email_bind_remind', 'email_verify', 'realperson_required', 'safe_mobile_required', 'device_grant_required', 'initialize_firebase', 'bbs_auth_login', 'fetch_instance_id', 'enable_flash_login'],
            'Player': ['disable_ysdk_guard', 'enable_announce_pic_popup', 'protocol', 'qr_enabled', 'qr_bbs', 'qr_cloud', 'enable_user_center', 'guardian_required', 'realname_required', 'heartbeat_required'],
            'Announce': ['remind', 'alert', 'extra_remind'],
            'Security': ['bcrypt_cost', 'token_length', 'min_password_len'],
            'Auth': ['enable_password_verify', 'enable_guest'],
            'Other': ['modified', 'serviceworker', 'new_register_page_enable', 'kcp_enable', 'enable_web_dpi', 'list_price_tierv2_enable'],
            'Dispatch': ['list'],
            'Crypto': ['rsa'],
            'Mail': ['ENABLE', 'MAIL_SERVER', 'MAIL_PORT', 'MAIL_USE_TLS', 'MAIL_USE_SSL', 'MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER']
        }
        for section, settings in required_settings.items():
            if section not in config:
                return False
            for setting in settings:
                if setting not in config[section]:
                    return False
        return True
    except FileNotFoundError:
        return False
    except yaml.YAMLError:
        return False

# 单独拎出来 检查region对不对
def check_region():
    for entry in get_config()['Gateserver']:
        if ('name' not in entry or not entry['name'] or
            'title' not in entry or not entry['title'] or
            'dispatchUrl' not in entry or not entry['dispatchUrl']):
            return False
    return True

# 检查dispatch_list 每个字段是不是空的 是空的你玩鸡毛
def check_dispatch():
    config = get_config()['Dispatch']
    if ('list' not in config or not isinstance(config['list'], dict)):
        return False
    for name, url in config['list'].items():
        if not isinstance(name, str) or not isinstance(url, str) or not url.startswith('http' or 'https'):
            return False
    return True