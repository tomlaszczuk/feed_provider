from flask import jsonify
from . import api
from ..models import SKU


@api.route('/sku/<stock_code>/', methods=['GET'])
def get_sku(stock_code):
    sku = SKU.query.filter_by(stock_code=stock_code).first()
    return jsonify(sku.to_json())


@api.route('/skus/', methods=['GET'])
def get_skus():
    skus = SKU.query.order_by(SKU.id)
    return jsonify({'skus': [sku.to_json() for sku in skus]})