from flask import url_for
from . import db
from .exceptions import ValidationError


def is_allowed_product_type(product_type):
    ALLOWED_TYPES = ('PHONE', 'TAB', 'RETAIL',
                     'MODEM', 'SIM_CARD', 'BUNDLE')
    return product_type in ALLOWED_TYPES


class Product(db.Model):
    __tablename__ = 'models'
    id = db.Column(db.Integer, primary_key=True)
    manufacturer = db.Column(db.String(128), index=True)
    model_name = db.Column(db.String(255), index=True)
    product_type = db.Column(db.String(32))
    skus = db.relationship('SKU', backref='base_product', lazy='dynamic')

    def get_full_product_name(self):
        return "%s %s" % (self.manufacturer, self.model_name)

    def to_json(self):
        json_product = {
            'id': self.id,
            'url': url_for('api.get_product', pk=self.id, _external=True),
            'manufacturer': self.manufacturer,
            'model_name': self.model_name,
            'product_type': self.product_type,
            'skus': [
                {
                    s.stock_code: url_for(
                        'api.get_sku', stock_code=s.stock_code, _external=True
                    )
                } for s in self.skus
            ],
            'sku_count': self.skus.count()
        }
        return json_product

    @staticmethod
    def from_json(json_product):
        manufacturer = json_product.get('manufacturer')
        model_name = json_product.get('model_name')
        product_type = json_product.get('product_type')
        if manufacturer is None or manufacturer == '' \
                or model_name is None or model_name == '':
            raise ValidationError(
                'Product does not have manufacturer or model name'
            )
        if not is_allowed_product_type(product_type):
            raise ValidationError(
                'Product type is not allowed'
            )
        return Product(manufacturer=manufacturer, model_name=model_name,
                       product_type=product_type)

    def __repr__(self):
        return self.get_full_product_name()


class SKU(db.Model):
    __tablename__ = 'skus'
    id = db.Column(db.Integer, primary_key=True)
    base_product_id = db.Column(db.Integer, db.ForeignKey('models.id'))
    stock_code = db.Column(db.String(255), unique=True, index=True)
    color = db.Column(db.String(32))
    photos = db.relationship('Photo', backref='sku', lazy='dynamic')
    offers = db.relationship('Offer', backref='sku', lazy='dynamic')
    availability = db.Column(db.String(32))

    def to_json(self):
        sku_json = {
            'id': self.id,
            'availability': self.availability,
            'url': url_for('api.get_sku', stock_code=self.stock_code,
                           _external=True),
            'stock_code': self.stock_code,
            'product': {
                self.base_product.get_full_product_name():
                url_for('api.get_product', pk=self.base_product_id,
                        _external=True)
            },
            'photos': [
                {'default': photo.default, 'url': photo.url}
                for photo in self.photos
            ],
            'offers': [
                {
                    offer.tariff_plan_code: url_for(
                        'api.get_offer', pk=offer.id, _external=True)
                }
                for offer in self.offers
            ]
        }
        return sku_json

    @staticmethod
    def from_json(json_sku):
        stock_code = json_sku.get('stock_code')
        if stock_code is None or stock_code == '':
            raise ValidationError('stock_code is missing')
        if json_sku.get('photos') is None or json_sku.get('photos') == []:
            raise ValidationError('sku cannot be saved without photos provided')
        return SKU(stock_code=stock_code)

    def __repr__(self):
        return self.stock_code


class Photo(db.Model):
    __tablename__ = 'photos'
    id = db.Column(db.Integer, primary_key=True)
    sku_id = db.Column(db.Integer, db.ForeignKey('skus.id'))
    url = db.Column(db.String(255))
    default = db.Column(db.Boolean, index=True)


class Offer(db.Model):
    __tablename__ = 'offers'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(32), index=True)
    segmentation = db.Column(db.String(64))
    market = db.Column(db.String(10))
    sku_id = db.Column(db.Integer, db.ForeignKey('skus.id'))
    price = db.Column(db.Float)
    old_price = db.Column(db.Float)
    abo_price = db.Column(db.Float)
    offer_url = db.Column(db.String(255), unique=True)
    tariff_plan_code = db.Column(db.String(16), index=True)
    offer_code = db.Column(db.String(16), index=True)
    contract_condition_code = db.Column(db.String(3), index=True)
    priority = db.Column(db.Integer)

    def set_prices(self, scrapped_price):
        if scrapped_price != self.price:
            self.old_price = self.price
            self.price = scrapped_price

    def map_category(self):
        if "TAB" in self.category:
            return "tablet-laptop"
        elif "MODEM" in self.category:
            return "modem-router"
        else:
            return "telefon"

    def build_url(self):
        domain = 'http://plus.pl/'
        portlet = self.map_category()
        device_type = self.sku.base_product.product_type
        segment = self.segmentation
        market = self.market
        contract = self.contract_condition_code
        tariff = self.tariff_plan_code
        offer = self.offer_code
        sku = self.sku.stock_code
        url = domain + portlet + '?deviceTypeCode=' + device_type \
            + "&deviceStockCode=" + sku + "&processSegmentationCode=" + segment \
            + "&marketTypeCode=" + market + "&contractConditionCode=" + contract \
            + "&tariffPlanCode=" + tariff + "&offerNSICode=" + offer
        return url

    def generate_category(self):
        return self.segmentation.replace(".", "-") + "-" \
            + self.sku.base_product.product_type

    def __init__(self, segmentation, market, sku, offer_code,
                 tariff_plan_code, contract_condition_code):
        self.segmentation = segmentation
        self.market = market
        self.sku = sku
        self.offer_code = offer_code
        self.tariff_plan_code = tariff_plan_code
        self.contract_condition_code = contract_condition_code
        self.category = self.generate_category()
        self.offer_url = self.build_url()

    def to_json(self):
        offer_json = {
            'id': self.id,
            'category': self.category,
            'segmentation': self.segmentation,
            'market': self.market,
            'product_price': self.price,
            'monthly_price': self.abo_price,
            'offer_nsi_code': self.offer_code,
            'tariff_plan_code': self.tariff_plan_code,
            'contract_condition': self.contract_condition_code,
            'product_page': self.offer_url,
            'sku': {
                self.sku.stock_code:
                    url_for('api.get_sku', stock_code=self.sku.stock_code,
                            _external=True)
            },
            'url': url_for('api.get_offer', pk=self.id, _external=True)
        }
        return offer_json

    def __repr__(self):
        return "%s; %s; %s; %s" % (
            self.sku.stock_code, self.offer_code,
            self.tariff_plan_code, self.contract_condition_code
        )