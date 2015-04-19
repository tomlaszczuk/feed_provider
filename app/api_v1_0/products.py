from flask import jsonify, request, url_for
from . import api
from .. import db
from ..models import Product


@api.route("/product/<int:pk>/", methods=['GET'])
def get_product(pk):
    product = Product.query.get(pk)
    return jsonify(product.to_json())


@api.route('/products/', methods=['GET'])
def get_products():
    products = Product.query.order_by(Product.id)
    return jsonify({'products': [product.to_json() for product in products]})


@api.route('/products/', methods=['POST'])
def post_product():
    req_json = request.get_json(force=True)
    product = Product.from_json(req_json)
    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_json()), 201, \
        {'Location': url_for('api.get_product', pk=product.id, _external=True)}