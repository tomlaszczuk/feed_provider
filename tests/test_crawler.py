import unittest
from config import config
from crawler.web_crawler import WebCrawler

from app import db, app
from app.models import Product, Photo, SKU, Offer


class CrawlerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config.from_object(config['testing'])
        self.crawler = WebCrawler(segment="IND.NEW.POSTPAID.ACQ")
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_offers_list_gatherer(self):
        offer_list = self.crawler.offer_list()
        self.assertIsNotNone(offer_list)
        one_offer = offer_list[0]
        self.assertIn("tariffPlanCode", one_offer)
        self.assertIn("offerNSICode", one_offer)
        self.assertIn("contractConditionCode", one_offer)
        self.assertIn("monthlyFeeGross", one_offer)

    def test_pages_info(self):
        offer = {
            "offerNSICode": "NSZAS24A",
            "tariffPlanCode": "15F2A",
            "contractConditionCode": "24A"
        }
        page_count = self.crawler.pages(offer=offer)
        self.assertIsInstance(page_count, int)

    def test_device_gatherer(self):
        offer = {
            "offerNSICode": "NSZAS24A",
            "tariffPlanCode": "15F2A",
            "contractConditionCode": "24A"
        }
        page = 5
        devices = self.crawler.gather_devices(offer=offer, page=page)
        device = devices[0]
        self.assertIn("brand", device)
        self.assertIn("devicePriority", device)
        self.assertIn("imagesOnDetails", device)
        self.assertTrue(len(device["imagesOnDetails"]) >= 1)
        self.assertIn("modelName", device)
        self.assertIn("sku", device)

    def test_saving_devices(self):
        # TODO Write this test
        offer_list = self.crawler.offer_list()
        offer = offer_list[0]
        devices = self.crawler.gather_devices(offer=offer, page=1)
        device = devices[0]
        self.crawler.save_or_update_device(device_info=device, offer_info=offer)
        self.assertEqual(Product.query.count(), 1)
        self.assertEqual(SKU.query.count(), 1)
        self.assertEqual(Offer.query.count(), 1)
        self.assertEqual(
            Photo.query.count(), len(device['imagesOnDetails'])
        )
        self.assertEqual(Photo.query.filter_by(default=True).count(), 1)

    def test_is_updating_existing_rows(self):
        offer_list = self.crawler.offer_list()
        offer = offer_list[0]
        devices = self.crawler.gather_devices(offer=offer, page=1)
        device = devices[0]
        self.crawler.save_or_update_device(device_info=device, offer_info=offer)

        device["prices"]["grossPrice"] = "1234,456"
        device["devicePriority"] = 20999
        device["imagesOnDetails"][0]["defaultImage"] = "false"
        device["imagesOnDetails"][1]["defaultImage"] = "true"
        offer["monthlyFeeGross"] = "654,321"
        self.crawler.save_or_update_device(device_info=device, offer_info=offer)
        self.assertEqual(Product.query.count(), 1)
        self.assertEqual(Offer.query.count(), 1)

        o = Offer.query.first()

        self.assertEqual(o.priority, 20999)
        self.assertEqual(o.abo_price, 654.321)
        self.assertEqual(o.price, 1234.456)
        self.assertIsNotNone(o.old_price)
        self.assertEqual(Photo.query.filter_by(default=True).count(), 1)