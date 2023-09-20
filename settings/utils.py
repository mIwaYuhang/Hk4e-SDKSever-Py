import requests
import bcrypt
import hashlib
import geoip2.database
import settings.define as define

from settings.config import get_config

def get_country_for_ip(ip):
   with geoip2.database.Reader(define.GEOIP2_DB_PATH) as reader:
      try:
         return reader.country(ip).country.iso_code
      except geoip2.errors.AddressNotFoundError:
         pass
      except geoip2.errors.GeoIP2Error as err:
         print(f"Unexpected {err=} while resolving country code for {ip=}")
         pass
   return None

def request_ip(request):
   return request.remote_addr

def chunked(size, source):
   for i in range(0, len(source), size):
      yield source[i:i+size]

def forward_request(request, url):
   return requests.get(url, headers={"miHoYoCloudClientIP": request_ip(request)}).content

# 密码保存
def password_hash(password):
   h = hashlib.new('sha256')
   h.update(password.encode())
   return bcrypt.hashpw(h.hexdigest().encode(), bcrypt.gensalt(rounds=get_config()["security"]["bcrypt_cost"]))

# 密码验证
def password_verify(password, hashed):
   h = hashlib.new('sha256')
   h.update(password.encode())
   return bcrypt.checkpw(h.hexdigest().encode(), hashed)

def mask_string(text):
   if len(text) < 4:
      return "*" * len(text)                          # 如果源小于4个字符，则将其全部屏蔽
   else:
      start_pos = 2 if len(text) >= 10 else 1         # 根据总长度，显示1或2个第一个字符
      end_post = 2 if len(text) > 5 else 1            # 显示最后2个字符，但前提是总长度大于5个字符
      return f"{text[0:start_pos]}****{text[len(text)-end_post:]}"

def mask_email(email):
   text = email.split('@')
   return f"{mask_string(text[0])}@{text[1]}"