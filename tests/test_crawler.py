import unittest
from config import config
from crawler.web_crawler import WebCrawler

from app import db, create_app
from app.models import Product, Photo, SKU, Offer


class CrawlerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.crawler = WebCrawler(segment="IND.NEW.POSTPAID.ACQ")
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_offers_list_gatherer(self):
        contract_conditions = self.crawler.available_contract_conditions()
        offer_list = self.crawler.offer_list(
            contract_conditions=contract_conditions
        )
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
            "tariffPlanCode": "5F20A",
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
        contract_conditions = self.crawler.available_contract_conditions()
        offer_list = self.crawler.offer_list(
            contract_conditions=contract_conditions
        )
        offer = offer_list[0]
        devices = self.crawler.gather_devices(offer=offer, page=1)
        device = devices[0]
        self.crawler.save_or_update_device(device_info=device, offer_info=offer)
        self.assertEqual(Product.query.count(), 1)
        self.assertEqual(SKU.query.count(), 1)
        self.assertIsNotNone(SKU.query.first().availability)
        self.assertEqual(Offer.query.count(), 1)
        self.assertEqual(
            Photo.query.count(), len(device['imagesOnDetails'])
        )
        self.assertEqual(Photo.query.filter_by(default=True).count(), 1)

    def test_is_updating_existing_rows(self):
        contract_conditions = self.crawler.available_contract_conditions()
        offer_list = self.crawler.offer_list(
            contract_conditions=contract_conditions
        )
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

    def test_another_sku(self):
        product = Product(manufacturer="LG", model_name="G2 Mini",
                          product_type="PHONE")
        sku = SKU(base_product=product, stock_code="lg-g2-mini-lte-black")
        offer = Offer(
            segmentation="IND.NEW.POSTPAID.ACQ",
            sku=sku, market="IND", offer_code="NSZAS24A",
            tariff_plan_code="5F20A", contract_condition_code="24A"
        )
        all_skus_codes = self.crawler._all_skus(offer.offer_url)
        self.assertTrue(len(all_skus_codes) > 1)
        self.assertIn('lg-g2-mini-lte-white', all_skus_codes)

    def test_save_unsaved_sku(self):
        product = Product(manufacturer="LG", model_name="G2 Mini",
                          product_type="PHONE")
        sku = SKU(base_product=product, stock_code="lg-g2-mini-lte-black")
        offer = Offer(
            segmentation="IND.NEW.POSTPAID.ACQ",
            sku=sku, market="IND", offer_code="NSZAS24A",
            tariff_plan_code="5F20A", contract_condition_code="24A"
        )
        db.session.add_all([product, sku, offer])
        db.session.commit()
        self.crawler.save_new_found_skus()
        self.assertTrue(len(Product.query.first().skus.all()) > 1)
        self.assertIn(
            SKU.query.filter_by(stock_code="lg-g2-mini-lte-white").first(),
            Product.query.first().skus
        )
        self.assertIsNotNone(
            SKU.query.filter_by(
                stock_code="lg-g2-mini-lte-white").first().availability
        )

    def test_not_inserting_existing_sku(self):
        product = Product(manufacturer="LG", model_name="G2 Mini",
                          product_type="PHONE")
        sku = SKU(base_product=product, stock_code="lg-g2-mini-lte-black")
        offer = Offer(
            segmentation="IND.NEW.POSTPAID.ACQ",
            sku=sku, market="IND", offer_code="NSZAS24A",
            tariff_plan_code="5F20A", contract_condition_code="24A"
        )
        db.session.add_all([product, sku, offer])
        db.session.commit()
        self.crawler.save_new_found_skus()
        self.assertEqual(
            SKU.query.filter_by(stock_code="lg-g2-mini-lte-black").count(), 1
        )

    def test_new_found_sku_has_the_same_offer_codes_as_saved_sku(self):
        product = Product(manufacturer="LG", model_name="G2 Mini",
                          product_type="PHONE")
        sku = SKU(base_product=product, stock_code="lg-g2-mini-lte-black")
        offer = Offer(
            segmentation="IND.NEW.POSTPAID.ACQ",
            sku=sku, market="IND", offer_code="NSZAS24A",
            tariff_plan_code="5F20A", contract_condition_code="24A"
        )
        db.session.add_all([product, sku, offer])
        db.session.commit()
        self.crawler.save_new_found_skus()
        self.assertTrue(Offer.query.count() > 1)
        for i in range(Offer.query.count()):
            self.assertEqual(Offer.query.get(i+1).offer_code, "NSZAS24A")

    def test_new_found_sku_has_photos(self):
        product = Product(manufacturer="LG", model_name="G2 Mini",
                          product_type="PHONE")
        sku = SKU(base_product=product, stock_code="lg-g2-mini-lte-black")
        offer = Offer(
            segmentation="IND.NEW.POSTPAID.ACQ",
            sku=sku, market="IND", offer_code="NSZAS24A",
            tariff_plan_code="5F20A", contract_condition_code="24A"
        )
        db.session.add_all([product, sku, offer])
        db.session.commit()
        self.crawler.save_new_found_skus()
        new_sku = SKU.query.filter_by(stock_code="lg-g2-mini-lte-white").first()
        self.assertTrue(new_sku.photos.count() >= 1)

    def test_new_found_sku_has_abo_price_and_device_price(self):
        product = Product(manufacturer="LG", model_name="G2 Mini",
                          product_type="PHONE")
        sku = SKU(base_product=product, stock_code="lg-g2-mini-lte-black")
        offer = Offer(
            segmentation="IND.NEW.POSTPAID.ACQ",
            sku=sku, market="IND", offer_code="NSZAS24A",
            tariff_plan_code="5F20A", contract_condition_code="24A"
        )
        offer.abo_price = 100.00
        offer.price = 90.00
        db.session.add_all([product, sku, offer])
        db.session.commit()
        self.crawler.save_new_found_skus()
        new_sku = SKU.query.filter_by(stock_code="lg-g2-mini-lte-white").first()
        new_offer = Offer.query.filter_by(sku=new_sku).first()
        self.assertEqual(new_offer.abo_price, 100.00)
        self.assertEqual(new_offer.price, 90.00)

    def test_sku_availability_is_string_representation(self):
        product = Product(manufacturer="LG", model_name="G2 Mini",
                          product_type="PHONE")
        sku = SKU(base_product=product, stock_code="lg-g2-mini-lte-black")
        offer = Offer(
            segmentation="IND.NEW.POSTPAID.ACQ",
            sku=sku, market="IND", offer_code="NSZAS24A",
            tariff_plan_code="5F20A", contract_condition_code="24A"
        )
        db.session.add_all([product, sku, offer])
        db.session.commit()
        self.crawler.save_new_found_skus()
        new_sku = SKU.query.filter_by(stock_code="lg-g2-mini-lte-white").first()
        self.assertIsInstance(new_sku.availability, str)
        self.assertIn(new_sku.availability,
                      ('AVAILABLE', 'NOT_AVAILABLE', 'RUNNING_OUT'))
