from flask import jsonify, request, url_for
from . import api
from .. import db
from ..models import SKU, Product, Photo


@api.route('/sku/<stock_code>/', methods=['GET'])
def get_sku(stock_code):
    sku = SKU.query.filter_by(stock_code=stock_code).first()
    return jsonify(sku.to_json())


@api.route('/skus/', methods=['GET'])
def get_skus():
    skus = SKU.query.order_by(SKU.id)
    return jsonify({'skus': [sku.to_json() for sku in skus]})


@api.route('/product/<int:pk>/skus/', methods=['POST'])
def post_sku(pk):
    product = Product.query.get(pk)
    sku_json = request.get_json(force=True)
    sku = SKU.from_json(sku_json)
    sku.base_product = product
    if sku_json.get('availability'):
        sku.availability = sku_json.get('availability')
    db.session.add(sku)
    for photo in sku_json['photos']:
        p = Photo(default=photo['default'], url=photo['url'], sku=sku)
        db.session.add(p)
    db.session.commit()
    return jsonify(sku.to_json()), 201, \
        {'Location': url_for('api.get_sku', stock_code=sku.stock_code,
                             _external=True)}
