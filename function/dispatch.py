from __main__ import app
import yaml
import settings.define as define
import data.proto.QueryRegionListHttpRsp_pb2 as RegionList

from flask import Response
from base64 import b64encode
from flask_caching import Cache
from settings.config import get_config

cache = Cache(app, config={'CACHE_TYPE': 'simple'})
@app.context_processor
def inject_config():
    config = get_config()
    return {'config': config}

with open(define.CONFIG_FILE_PATH, 'r', encoding="utf-8") as f:
    config = yaml.safe_load(f)
with open(define.DISPATCH_KEY, 'rb') as f:
    dispatch_key = f.read()
with open(define.DISPATCH_SEED, 'rb') as f:
    dispatch_seed = f.read()

#=====================Dispatch配置=====================#
# 实验性分区 Dispatch
# version=CNRELWin4.0.1 lang=2 platform=3 binary=1 time=291 channel_id=1 sub_channel_id=1
# version=OSRELWin2.8.0 lang=2 platform=3 binary=1 time=454 channel_id=1 sub_channel_id=1
@app.route('/query_region_list', methods=['GET'])
def query_dispatch():
    response = RegionList.QueryRegionListHttpRsp()
    response.retcode = define.RES_SUCCESS
    for entry in config['Gateserver']:
        region_info = response.region_list.add()
        region_info.name = entry['name']
        region_info.title = entry['title']
        region_info.type = "DEV_PUBLIC"
        region_info.dispatch_url = entry['dispatchUrl']
    custom_config = '{"sdkenv":"0","checkdevice":"false","loadPatch":"false","showexception":"false","regionConfig":"pm|fk|add","downloadMode":"0"}'
    encrypted_config = bytearray()
    for coke in range(len(custom_config)):
        encrypted_config.append(ord(custom_config[coke]) ^ dispatch_key[coke % len(dispatch_key)])
    updated_region_list = RegionList.QueryRegionListHttpRsp()
    updated_region_list.region_list.extend(response.region_list)
    updated_region_list.client_secret_key = dispatch_seed
    updated_region_list.client_custom_config_encrypted = bytes(encrypted_config)
    updated_region_list.enable_login_pc = True      # 试过了 无论是否都没用 但是必须要存在 :)
    # 序列化
    serialized_data = updated_region_list.SerializeToString()
    base64_str = b64encode(serialized_data).decode()
    return Response(base64_str, content_type='text/plain')
# 实验性解析QueryCurRegion(暂时留空 先不写)
# version=OSRELWin2.8.0 lang=2 platform=3 binary=1 time=348 channel_id=1 sub_channel_id=1 account_type=1 dispatchSeed=caffbdd6d7460dff key_id=3
@app.route('/query_region/<name>', methods=['GET'])
@app.route('/query_cur_region/<name>', methods=['GET'])
def query_cur_region():
    return "Not found"

'''
全局dispatch (转发到dispatch后返回结果)
@app.route('/query_region_list', methods=['GET'])
def query_region_list():
    try:
        return forward_request(request, f"{get_config()['Dispatch']['global']}/query_region_list?{request.query_string.decode()}")
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=} while forwarding request")
        abort(500)
解析dispatch
@app.route('/query_region/<name>', methods=['GET'])
def query_cur_region(name):
    try:
        return forward_request(request, f"{get_config()['Dispatch']['local'][name]}/query_cur_region?{request.query_string.decode()}")
    except KeyError:
        print(f"未知的region={name}")
        abort(404)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=} while forwarding request")
        abort(500)
'''