from . import db


class Product(db.Model):
    __tablename__ = 'models'
    id = db.Column(db.Integer, primary_key=True)
    manufacturer = db.Column(db.String(128), index=True)
    model_name = db.Column(db.String(255), index=True)
    product_type = db.Column(db.String(32))
    skus = db.relationship('SKU', backref='base_product', lazy='dynamic')

    def __repr__(self):
        return self.manufacturer + self.model_name


class SKU(db.Model):
    __tablename__ = 'skus'
    id = db.Column(db.Integer, primary_key=True)
    base_product_id = db.Column(db.Integer, db.ForeignKey('models.id'))
    stock_code = db.Column(db.String(255), unique=True, index=True)
    color = db.Column(db.String(32))
    photos = db.relationship('Photo', backref='sku', lazy='dynamic')
    offers = db.relationship('Offer', backref='sku', lazy='dynamic')
    availability = db.Column(db.Boolean)

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
        if 'TABLET' in self.category:
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

    def __init__(self, category, segmentation, market, sku, offer_code,
                 tariff_plan_code, contract_condition_code):
        self.category = category
        self.segmentation = segmentation
        self.market = market
        self.sku = sku
        self.offer_code = offer_code
        self.tariff_plan_code = tariff_plan_code
        self.contract_condition_code = contract_condition_code
        self.offer_url = self.build_url()

    def __repr__(self):
        return "%s; %s; %s; %s" % (
            self.sku.stock_code, self.offer_code,
            self.tariff_plan_code, self.contract_condition_code
        )