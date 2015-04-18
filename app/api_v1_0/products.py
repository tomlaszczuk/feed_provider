from flask import jsonify
from . import api
from ..models import Product


@api.route("/product/<int:pk>/")
def get_product(pk):
    product = Product.query.get(pk)
    return jsonify(product.to_json())


@api.route('/products/')
def get_products():
    products = Product.query.all()
    return jsonify({'products': [product.to_json() for product in products]})