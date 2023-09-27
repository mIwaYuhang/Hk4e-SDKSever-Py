from __main__ import app
import json
import settings.repositories as repositories

from flask import abort, request
from settings.database import get_db
from settings.response import json_rsp

#=====================GameServer请求处理=====================#
# 玩家登入
@app.route('/inner/bat/game/gameLoginNotify', methods = ['POST'])
# @ip_whitelist(['192.168.1.8'])
def player_login():
   cursor = get_db().cursor()
   player_info = json.loads(request.data.decode())
   uid = player_info['uid']
   account_type = player_info['account_type']
   account = player_info['account']
   platform = player_info['platform']
   region = player_info['region']
   biz_game = player_info['biz_game']
    
   try:
      cursor.execute('INSERT INTO `accounts_events` (`uid`, `method`, `account_type`, `account_id`, `platform`, `region`, `biz_game`, `epoch_created`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', (uid, 'LOGIN', account_type, account, platform, region, biz_game, int(epoch())))
   except Exception as err:
      print(f"处理用户登入事件时出现意外错误{err=}, {type(err)=}")
   return json_rsp(repositories.RES_SUCCESS, {})

# 玩家登出
@app.route('/inner/bat/game/gameLogoutNotify', methods = ['POST'])
def player_logout():
   cursor = get_db().cursor()
   player_info = json.loads(request.data.decode())
   uid = player_info['uid']
   account_type = player_info['account_type']
   account = player_info['account']
   platform = player_info['platform']
   region = player_info['region']
   biz_game = player_info['biz_game']
   try:
      cursor.execute('INSERT INTO `accounts_events` (`uid`, `method`, `account_type`, `account_id`, `platform`, `region`, `biz_game`, `epoch_created`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', (uid, 'LOGOUT', account_type, account, platform, region, biz_game, int(epoch())))
   except Exception as err:
      print(f"处理用户登出事件时出现意外错误{err=}, {type(err)=}")
   return json_rsp(repositories.RES_SUCCESS, {})

# 心跳包
@app.route('/inner/bat/game/gameHeartBeatNotify', methods = ['POST'])
def player_heartbeat():
   print(request.data)
   try:
      return json_rsp(repositories.RES_SUCCESS, {})
   except Exception as err:
      print(f"处理心跳包时出现意外错误{err=}, {type(err)=}")
      abort(500)
