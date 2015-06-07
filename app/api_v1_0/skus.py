from flask import jsonify, request, url_for, abort
from . import api
from .. import db
from ..models import SKU, Product, Photo


@api.route('/sku/<stock_code>/', methods=['GET'])
def get_sku(stock_code):
    sku = SKU.query.filter_by(stock_code=stock_code).first()
    if not sku:
        abort(404)
    return jsonify(sku.to_json())


@api.route('/skus/', methods=['GET'])
def get_skus():
    skus = SKU.query.order_by(SKU.id)
    return jsonify({'skus': [sku.to_json() for sku in skus]})


@api.route('/product/<int:pk>/skus/', methods=['GET'])
def get_skus_for_product(pk):
    product = Product.query.get_or_404(pk)
    skus = SKU.query.filter_by(base_product=product).order_by(SKU.id)
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


@api.route('/sku/<stock_code>/', methods=['PUT'])
def edit_sku(stock_code):
    sku = SKU.query.filter_by(stock_code=stock_code).first()
    req_json = request.get_json(force=True)
    sku.availability = req_json.get('availability', sku.availability)
    photos = req_json.get('photos')
    for photo in photos:
        if photo.get('default') is False and photo.get('url'):
            p = Photo(default=False, url=photo['url'], sku=sku)
            db.session.add(p)
        elif photo.get('default') is True and photo.get('url'):
            p = Photo.query.filter_by(sku=sku, default=True).first()
            p.url = photo['url']
            db.session.add(p)
    db.session.commit()
    return jsonify(sku.to_json()), 200