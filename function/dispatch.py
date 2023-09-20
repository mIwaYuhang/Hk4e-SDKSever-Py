from __main__ import app
from flask_caching import Cache
from flask import request, abort
from settings.config import get_config
from settings.utils import forward_request

cache = Cache(app, config={'CACHE_TYPE': 'simple'})
@app.context_processor
def inject_config():
    config = get_config()
    return {'config': config}

#=====================Dispatch配置=====================#
# 全局dispatch
@app.route('/query_region_list', methods=['GET'])
def query_region_list():
    try:
        return forward_request(request, f"{get_config()['dispatch']['global']}/query_region_list?{request.query_string.decode()}")
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=} while forwarding request")
        abort(500)

# 解析dispatch
@app.route('/query_region/<name>', methods=['GET'])
def query_cur_region(name):
    try:
        return forward_request(request, f"{get_config()['dispatch']['local'][name]}/query_cur_region?{request.query_string.decode()}")
    except KeyError:
        print(f"未知的region={name}")
        abort(404)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=} while forwarding request")
        abort(500)