import json
import unittest
from flask import url_for
from app import create_app, db
from app.models import Product, Photo, Offer, SKU


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_product(self):
        p = Product(manufacturer="Nokia", model_name="Lumia 520",
                    product_type="PHONE")
        sku_1 = SKU(base_product=p, stock_code="nokia-lumia-520-black",
                    availability="AVAILABLE")
        sku_2 = SKU(base_product=p, stock_code="nokia-lumia-520-red",
                    availability="AVAILABLE")
        db.session.add_all([p, sku_1, sku_2])
        db.session.commit()

        # get product
        response = self.client.get(url_for('api.get_product', pk=1))
        self.assertEqual(response.status_code, 200)

        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response["manufacturer"], "Nokia")
        self.assertEqual(json_response["model_name"], "Lumia 520")
        self.assertIsInstance(json_response["skus"], list)
        self.assertEqual(len(json_response["skus"]), 2)
        self.assertIn("nokia-lumia-520-black", json_response["skus"][0])