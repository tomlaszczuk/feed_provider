import datetime
import json
import requests
from config import Config

from app import db
from app.models import Offer, Photo, Product, SKU


class WebCrawler:
    def __init__(self, segment):
        self.segment = segment
        self.request_counter = 0

    def offer_list(self):
        r = requests.post(Config.DEVICE_LIST,
                          data={"processSegmentationCode": self.segment})
        self.request_counter += 1
        devices_json = r.json()
        offers = devices_json['rotator']
        return offers

    def pages(self, offer):
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

    def save_or_update_device(self, device_info, offer_info):
        product = Product(
            manufacturer=device_info["brand"],
            model_name=device_info["modelName"],
            priority=device_info["devicePriority"],
            product_type=device_info["productType"]
        )
        sku = SKU(base_product=product, stock_code=device_info["sku"])
        for photo in device_info["imagesOnDetails"]:
            device_photo = Photo(sku=sku, url=photo["normalImage"],
                                 default=photo["defaultImage"])
            db.session.add(device_photo)
        offer = Offer(
            category=offer_info["offerSegmentationCode"],
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
        offer.availability = device_info["available"]
        offer.abo_price = float(offer_info["monthlyFeeGross"].replace(",", "."))

        db.session.add(product)
        db.session.add(sku)
        db.session.add(offer)
        db.session.commit()

    def save_request_counter(self):
        with open("logs/request_counter.txt", "a") as request_counter:
            now = str(datetime.datetime.now())
            segment = self.segment
            req = self.request_counter
            request_counter.write("%s; %s; %d" % (now, segment, req))
