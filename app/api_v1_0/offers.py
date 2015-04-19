from flask import jsonify
from . import api
from ..models import Offer


@api.route('/offer/<int:pk>/')
def get_offer(pk):
    offer = Offer.query.get(pk)
    return jsonify(offer.to_json())


@api.route('/offers/')
def get_offers():
    offers = Offer.query.order_by(Offer.id)
    return jsonify({'offers': [offer.to_json() for offer in offers]})