import unittest
from app import app, db
from app.models import Product, Photo, Offer, SKU
from config import config


class OfferModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config.from_object(config['testing'])
        db.create_all()
        self.phone = Product(manufacturer='LG', model_name='G2 mini LTE',
                             product_type='PHONE')
        self.phone_variant = SKU(stock_code='lg-g2-mini-lte-black',
                                 base_product=self.phone)

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_product_url_builder(self):
        offer = Offer(category='Nowy numer',
                      segmentation='IND.NEW.POSTPAID.ACQ',
                      market='IND',
                      sku=self.phone_variant,
                      offer_code='XLINS24A',
                      tariff_plan_code='14L70',
                      contract_condition_code='24A')

        self.assertIsNotNone(offer.offer_url)
        self.assertEqual(offer.offer_url,
                         "http://plus.pl/telefon?deviceTypeCode=PHONE&"
                         "deviceStockCode=lg-g2-mini-lte-black&"
                         "processSegmentationCode=IND.NEW.POSTPAID.ACQ&"
                         "marketTypeCode=IND&contractConditionCode=24A&"
                         "tariffPlanCode=14L70&offerNSICode=XLINS24A"
                         )

        offer = Offer(category='Nowy numer TABLET',
                      segmentation='IND.NEW.POSTPAID.ACQ',
                      market='IND',
                      sku=self.phone_variant,
                      offer_code='XLINS24A',
                      tariff_plan_code='14L70',
                      contract_condition_code='24A')

        self.assertEqual(offer.offer_url,
                         "http://plus.pl/tablet-laptop?deviceTypeCode=PHONE&"
                         "deviceStockCode=lg-g2-mini-lte-black&"
                         "processSegmentationCode=IND.NEW.POSTPAID.ACQ&"
                         "marketTypeCode=IND&contractConditionCode=24A&"
                         "tariffPlanCode=14L70&offerNSICode=XLINS24A"
                         )

    def test_price_updates(self):
        offer = Offer(category='Nowy numer TABLET',
                      segmentation='IND.NEW.POSTPAID.ACQ',
                      market='IND',
                      sku=self.phone_variant,
                      offer_code='XLINS24A',
                      tariff_plan_code='14L70',
                      contract_condition_code='24A',
                      )

        offer.price = 1.23
        offer.set_prices(3.00)
        self.assertEqual(offer.price, 3.00)
        self.assertEqual(offer.old_price, 1.23)
        offer.set_prices(3.00)
        self.assertEqual(offer.old_price, 1.23)
