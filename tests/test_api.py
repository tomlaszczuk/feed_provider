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

    def test_get_skus(self):
        p = Product(manufacturer="Nokia", model_name="Lumia 520",
                    product_type="PHONE")
        sku_1 = SKU(base_product=p, stock_code="nokia-lumia-520-black",
                    availability="AVAILABLE")
        sku_2 = SKU(base_product=p, stock_code="nokia-lumia-520-red",
                    availability="NOT_AVAILABLE")
        photo_1 = Photo(sku=sku_1, default=True, url="http://some-photo.com")
        photo_2 = Photo(sku=sku_2, default=True, url="http://some-photo.com")
        offer_1 = Offer(
            segmentation="IND.NEW.POSTPAID.ACQ",
            sku=sku_1, market="IND", offer_code="NSZAS24A",
            tariff_plan_code="15F2F", contract_condition_code="24A"
        )
        offer_2 = Offer(
            segmentation="IND.NEW.POSTPAID.ACQ",
            sku=sku_1, market="IND", offer_code="NSZAS24A",
            tariff_plan_code="15F3F", contract_condition_code="24A"
        )

        db.session.add_all([sku_1, sku_2, photo_1, photo_2, offer_1, offer_2])
        db.session.commit()

        # get sku
        response = self.client.get(url_for('api.get_sku',
                                           stock_code=sku_1.stock_code))
        self.assertEqual(response.status_code, 200)

        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response["stock_code"], "nokia-lumia-520-black")
        self.assertIsInstance(json_response["photos"], list)
        self.assertEqual(len(json_response["photos"]), 1)
        self.assertEqual(json_response["availability"], "AVAILABLE")
        self.assertIsInstance(json_response["offers"], list)
        self.assertEqual(len(json_response["offers"]), 2)

        response = self.client.get(url_for('api.get_sku',
                                           stock_code=sku_2.stock_code))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(len(json_response["offers"]), 0)

    def test_post_product(self):
        # create new product
        response = self.client.post(
            url_for('api.post_product'),
            data=json.dumps({
                'manufacturer': 'Super Brand',
                'model_name': 'Model 2000',
                'product_type': 'PHONE'
            })
        )
        self.assertEqual(response.status_code, 201)
        url = response.headers.get('Location')
        self.assertIsNotNone(url)

        # get this product
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['url'], url)
        self.assertEqual(json_response['manufacturer'], 'Super Brand')
        self.assertEqual(json_response['model_name'], 'Model 2000')
        self.assertEqual(len(json_response['skus']), 0)

        # post not allowed product
        response = self.client.post(
            url_for('api.post_product'),
            data=json.dumps({
                'manufacturer': 'Super Brand',
                'model_name': 'Model 2010',
                'product_type': 'Radio'
            })
        )
        self.assertEqual(response.status_code, 400)

    def test_post_sku(self):
        # create new product
        p = Product(manufacturer='LG', model_name='G2 Mini',
                    product_type='PHONE')
        db.session.add(p)
        db.session.commit()

        # create new sku for that product
        stock_code = 'lg-g2-mini-lte-black'
        response = self.client.post(
            url_for('api.post_sku', pk=p.id),
            data=json.dumps({
                'stock_code': stock_code,
                'availability': 'AVAILABLE',
                'photos': [
                    {'default': True, 'url': 'http://some.photo.com'},
                    {'default': False, 'url': 'http://another.photo.com'}
                ]
            })
        )
        self.assertEqual(response.status_code, 201)
        url = response.headers.get('Location')
        self.assertIsNotNone(url)

        # get newly created sku
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['url'], url)
        self.assertEqual(json_response['stock_code'], stock_code)
        self.assertEqual(len(json_response['photos']), 2)

        # check if photos are saved in database
        self.assertEqual(Photo.query.count(), 2)

        # get product and assure that we see newly created sku
        response = self.client.get(url_for('api.get_product', pk=p.id))
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(len(json_response['skus']), 1)

        self.assertEqual(json_response['skus'][0][stock_code],
                         url_for('api.get_sku', stock_code=stock_code,
                                 _external=True))

    def test_post_offer(self):
        # create new product
        p = Product(manufacturer='LG', model_name='G2 Mini',
                    product_type='PHONE')
        # create new sku for that product
        sku = SKU(stock_code='lg-g2-mini-black', base_product=p)
        db.session.add_all([p, sku])
        db.session.commit()

        # post new offer
        response = self.client.post(
            url_for('api.post_offer', stock_code=sku.stock_code),
            data=json.dumps({
                'segmentation': 'IND.NEW.POSTPAID.ACQ',
                'tariff_plan_code': '14L60',
                'offer_nsi_code': 'XLINS24A',
                'contract_condition': '24A',
                'monthly_price': 100.00,
                'product_price': 90.00
            })
        )
        self.assertEqual(response.status_code, 201)
        url = response.headers.get('Location')
        self.assertIsNotNone(url)

        # get new offer
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['url'], url)
        self.assertEqual(json_response['market'], 'IND')
        self.assertEqual(json_response['offer_nsi_code'], 'XLINS24A')
        self.assertEqual(json_response['tariff_plan_code'], '14L60')
        self.assertIn(sku.stock_code, json_response['sku'].keys())
        self.assertIsNotNone(json_response['product_page'])
        self.assertIsNotNone(json_response['category'])

        # post new offer with the same tariff plan, but without monthly_fee
        ## monthly price should be the same as above
        response = self.client.post(
            url_for('api.post_offer', stock_code=sku.stock_code),
            data=json.dumps({
                'segmentation': 'IND.NEW.POSTPAID.ACQ',
                'tariff_plan_code': '14L60',
                'offer_nsi_code': 'XLINS24B',
                'contract_condition': '24A',
                'product_price': 90.00
            })
        )
        url = response.headers.get('Location')
        response = self.client.get(url)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['monthly_price'], 100.00)

        # post new offer with new tariff plan and without monthly_fee
        ## it should return bad request
        response = self.client.post(
            url_for('api.post_offer', stock_code=sku.stock_code),
            data=json.dumps({
                'segmentation': 'IND.NEW.POSTPAID.ACQ',
                'tariff_plan_code': '14L90',
                'offer_nsi_code': 'XLINS24B',
                'contract_condition': '24A',
                'product_price': 90.00
            })
        )
        self.assertEqual(response.status_code, 400)