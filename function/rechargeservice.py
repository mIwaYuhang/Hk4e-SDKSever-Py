from __main__ import app
import os
import settings.repositories as repositories

from flask import send_file
from flask_caching import Cache
from settings.loadconfig import get_config

cache = Cache(app, config={'CACHE_TYPE': 'simple'})
@app.context_processor
def inject_config():
    config = get_config()
    return {'config': config}

#=====================支付模块=====================#
# 支付窗口-美元(我怎么没抓到过这个？)
@app.route('/hk4e_cn/mdk/shopwindow/shopwindow/listPriceTier', methods = ['POST'])
@app.route('/hk4e_cn/mdk/shopwindow/shopwindow/listPriceTierV2', methods = ['POST'])
@app.route('/hk4e_global/mdk/shopwindow/shopwindow/listPriceTier', methods = ['POST'])
@app.route('/hk4e_global/mdk/shopwindow/shopwindow/listPriceTierV2', methods = ['POST'])
def price_tier_serve():
    file_path = repositories.SHOPWINDOW_TIERS_PATH
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return "Not found"

# 支付方式
@app.route('/hk4e_cn/mdk/tally/tally/listPayPlat', methods = ['POST'])
@app.route('/hk4e_global/mdk/tally/tally/listPayPlat', methods = ['POST'])
def price_pay_types_serve():
    file_path = repositories.SHOPWINDOW_PAY_TYPES_PATH
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return "Not found"