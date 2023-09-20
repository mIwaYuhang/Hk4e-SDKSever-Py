from __main__ import app
import json
import settings.define as define

from flask_caching import Cache
from settings.response import json_rsp_with_msg
from settings.config import get_config

cache = Cache(app, config={'CACHE_TYPE': 'simple'})
@app.context_processor
def inject_config():
    config = get_config()
    return {'config': config}

#=====================支付模块=====================#
# 支付窗口-美元(我怎么没抓到过这个？)
@app.route('/hk4e_cn/mdk/shopwindow/shopwindow/listPriceTier', methods=['POST'])
@app.route('/hk4e_global/mdk/shopwindow/shopwindow/listPriceTier', methods=['POST'])
def price_tier_serve():
    f = open(define.SHOPWINDOW_TIERS_PATH)
    tiers = json.load(f)
    f.close()
    currency = 'USD'
    return json_rsp_with_msg(define.RES_SUCCESS, "OK", {
        "data": {
            "suggest_currency": currency,
            "tiers": tiers[currency]
        }
    })