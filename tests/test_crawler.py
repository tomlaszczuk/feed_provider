import unittest
from config import config
from crawler.web_crawler import WebCrawler


class CrawlerTestCase(unittest.TestCase):
    def setUp(self):
        self.crawler = WebCrawler(segment="IND.NEW.POSTPAID.ACQ")

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
        self.assertTrue(len(device["images"]) >= 1)
        self.assertIn("modelName", device)
        self.assertIn("sku", device)