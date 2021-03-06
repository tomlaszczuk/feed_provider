import datetime
import json
import requests
from bs4 import BeautifulSoup as Soup

from app import db
from app.models import Offer, Photo, Product, SKU
from config import Config


class WebCrawler:
    def __init__(self, segment):
        self.segment = segment
        self.request_counter = 0
        self.scrapping_time = datetime.datetime.utcnow()

    def available_contract_conditions(self):
        contract_conditions = []
        r = requests.post(Config.DEVICE_LIST,
                          data={"processSegmentationCode": self.segment})
        self.request_counter += 1
        devices_json = r.json()
        available_cc = devices_json['pageInfo']['availableContractConditions']
        for cc in available_cc:
            contract_conditions.append(cc["value"].split()[0] + "A")
        return contract_conditions

    def offer_list(self, contract_conditions):
        offers = []
        for contract_condition in contract_conditions:
            r = requests.post(
                Config.DEVICE_LIST,
                data={
                    "processSegmentationCode": self.segment,
                    "contractConditionCode": contract_condition
                }
            )
            self.request_counter += 1
            devices_json = r.json()
            offers.extend(devices_json['rotator'])
        return offers

    def mark_inactive_offers(self, offer_codes_list):
        """
        :param offer_list: list of scrapped offer codes in segmentation
        """
        for offer in Offer.query.filter_by(segmentation=self.segment).all():
            if offer.offer_code not in offer_codes_list:
                offer.is_active = False
                db.session.add(offer)
        db.session.commit()

    def pages(self, offer):
        """
        param: offer - one offer from offer list scrapped by offer_list method
        """
        r = requests.post(
            Config.DEVICE_LIST,
            data={"processSegmentation": self.segment,
                  "offerNSICode": offer["offerNSICode"],
                  "tariffPlanCode": offer["tariffPlanCode"],
                  "contractConditionCode": offer["contractConditionCode"]}
        )
        self.request_counter += 1
        offer_json = r.json()
        return offer_json['pageInfo']['pages']

    def gather_devices(self, offer, page):
        r = requests.post(
            Config.DEVICE_LIST,
            data={"processSegmentation": self.segment,
                  "offerNSICode": offer["offerNSICode"],
                  "tariffPlanCode": offer["tariffPlanCode"],
                  "contractConditionCode": offer["contractConditionCode"],
                  "page": page}
        )
        self.request_counter += 1
        devices_json = r.json()
        return devices_json["devices"]

    def _all_skus(self, product_url):
        """
        Slow. Many requests. Use only when necessary
        Find all skus for given product url
        """
        r = requests.get(url=product_url)
        self.request_counter += 1
        html = r.content
        parsed_html = Soup(html)
        skus = parsed_html.find_all('input', attrs={'name': 'color'})
        return [sku['device-skus'] for sku in skus]

    def find_all_photos(self, offer):
        r = requests.get(url=offer.offer_url)
        self.request_counter += 1
        html = r.content
        parsed_html = Soup(html)
        photo_container = parsed_html.find('div',
                                           attrs={'id': 'phone-carousel'})
        imgs = photo_container.find_all('img')
        main_photo = Photo(sku=offer.sku, url=imgs[0].attrs['src'],
                           default=True)
        db.session.add(main_photo)
        for img in imgs[1:]:
            photo = Photo(sku=offer.sku, url=img.attrs['src'], default=False)
            db.session.add(photo)
        db.session.commit()

    def save_or_update_device(self, device_info, offer_info):
        # =================== Product ======================= #
        product = Product.query.filter_by(
            manufacturer=device_info["brand"],
            model_name=device_info["modelName"]
        ).first()
        if not product:
            product = Product(
                manufacturer=device_info["brand"],
                model_name=device_info["modelName"],
                product_type=device_info["productType"]
            )

        # =================== SKU ======================= #
        sku = SKU.query.filter_by(stock_code=device_info["sku"]).first()
        if not sku:
            sku = SKU(base_product=product, stock_code=device_info["sku"])
        sku.availability = device_info["available"]
        # =================== Photo ======================= #
        for photo in device_info["imagesOnDetails"]:
            device_photo = Photo.query.filter_by(
                url=photo["normalImage"]).first()
            if device_photo is not None:
                device_photo.default = photo["defaultImage"]
            else:
                device_photo = Photo(sku=sku, url=photo["normalImage"],
                                     default=photo["defaultImage"])
            db.session.add(device_photo)

        # =================== Offer ======================= #
        offer = Offer.query.filter_by(
            segmentation=self.segment,
            offer_code=offer_info["offerNSICode"],
            sku=sku,
            tariff_plan_code=offer_info["tariffPlanCode"],
            contract_condition_code=offer_info["contractConditionCode"]
        ).first()
        if not offer:
            offer = Offer(
                segmentation=self.segment,
                market=self.segment.split(".")[0],
                sku=sku,
                offer_code=offer_info["offerNSICode"],
                tariff_plan_code=offer_info["tariffPlanCode"],
                contract_condition_code=offer_info["contractConditionCode"]
            )
        offer.set_prices(
            float(device_info["prices"]["grossPrice"].replace(",", "."))
        )
        offer.abo_price = float(offer_info["monthlyFeeGross"].replace(",", "."))
        offer.priority = device_info["devicePriority"]

        # =================== Saving ======================= #
        db.session.add(product)
        db.session.add(sku)
        offer.ping(self.scrapping_time)
        db.session.commit()

    def _create_offers_with_new_sku(self, offer_list, sku):
        for offer in offer_list:
            r = requests.post(
                url=Config.DEVICE_PRICES,
                data={"processSegmentationCode": offer.segmentation,
                      "deviceStockCode": sku.stock_code,
                      "offerNSICode": offer.offer_code,
                      "tariffPlanCode": offer.tariff_plan_code,
                      "contractConditionCode": offer.contract_condition_code}
            )
            self.request_counter += 1
            if r.json()["devicesPrices"]:
                new_offer = Offer(
                    segmentation=offer.segmentation,
                    market=offer.market,
                    contract_condition_code=offer.contract_condition_code,
                    sku=sku,
                    tariff_plan_code=offer.tariff_plan_code,
                    offer_code=offer.offer_code
                )
                new_offer.priority = offer.priority
                new_offer.set_prices(offer.price)
                new_offer.abo_price = offer.abo_price
                db.session.add(new_offer)
        db.session.commit()

    def save_new_found_skus(self):
        for product in Product.query.all():
            saved_sku = product.skus.first()
            offers_for_saved_sku = Offer.query.filter_by(sku=saved_sku).all()
            all_skus = self._all_skus(offers_for_saved_sku[0].offer_url)
            for found_sku in all_skus:
                sku = SKU.query.filter_by(stock_code=found_sku).first()
                if not sku:
                    sku = SKU(stock_code=found_sku, base_product=product)
                    sku.availability = self.check_availability(sku.stock_code)
                    self._create_offers_with_new_sku(offers_for_saved_sku, sku)
                    new_offer = Offer.query.filter_by(sku=sku).first()
                    self.find_all_photos(new_offer)
                    db.session.add(sku)
        db.session.commit()

    def check_availability(self, sku_stock_code):
        r = requests.post(url=Config.DEVICE_AVAILABLE,
                          data={"deviceStockCode": sku_stock_code})
        self.request_counter += 1
        return r.json()["deviceAvailables"][0]["available"]

    def update_availability(self):
        """Used in a daily availability check"""
        for sku in SKU.query.all():
            sku.availability = self.check_availability(sku.stock_code)
            db.session.add(sku)
        db.session.commit()

    def save_request_counter(self):
        with open("logs/request_counter.txt", "a") as request_counter:
            now = str(datetime.datetime.now())
            segment = self.segment
            req = self.request_counter
            request_counter.write("\n%s; %s; %d" % (now, segment, req))
