from flask import jsonify
from . import api
from ..models import SKU


@api.route('/sku/<stock_code>/')
def get_sku(stock_code):
    sku = SKU.query.filter_by(stock_code=stock_code).first()
    return jsonify(sku.to_json())