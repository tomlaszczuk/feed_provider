from flask import jsonify, request, url_for
from . import api
from .. import db
from ..models import Offer, SKU
from ..exceptions import ValidationError


@api.route('/offer/<int:pk>/', methods=['GET'])
def get_offer(pk):
    offer = Offer.query.get(pk)
    return jsonify(offer.to_json())


@api.route('/offers/', methods=['GET'])
def get_offers():
    offers = Offer.query.order_by(Offer.id)
    return jsonify({'offers': [offer.to_json() for offer in offers]})


@api.route('/sku/<stock_code>/offers', methods=['GET'])
def get_offers_for_sku(stock_code):
    sku = SKU.query.filter_by(stock_code=stock_code).first()
    offers = Offer.query.filter_by(sku=sku).order_by(Offer.id)
    return jsonify({'offers': [offer.to_json() for offer in offers]})


@api.route('/sku/<stock_code>/offers/', methods=['POST'])
def post_offer(stock_code):
    sku = SKU.query.filter_by(stock_code=stock_code).first()
    offer_json = request.get_json(force=True)
    offer_json = Offer.validate_offer_json(offer_json)
    offer = Offer(
        segmentation=offer_json['segmentation'],
        market=offer_json['segmentation'].split('.')[0],
        sku=sku,
        offer_code=offer_json['offer_nsi_code'],
        tariff_plan_code=offer_json['tariff_plan_code'],
        contract_condition_code=offer_json['contract_condition'],
    )
    offer.set_prices(offer_json['product_price'])
    offer.abo_price = offer_json['monthly_price']
    offer.priority = 1
    db.session.add(offer)
    db.session.commit()
    return jsonify(offer.to_json()), 201, \
        {'Location': url_for('api.get_offer', pk=offer.id,
                             _external=True)}


@api.route('/offer/<int:pk>/', methods=['PUT'])
def edit_offer(pk):
    offer = Offer.query.get(pk)
    req_json = request.get_json(force=True)
    offer.category = req_json.get('category', offer.category)
    offer.priority = req_json.get('priority', offer.priority)
    if req_json.get('product_price'):
        offer.set_prices(req_json['product_price'])
    db.session.add(offer)
    db.session.commit()
    return jsonify(offer.to_json()), 200