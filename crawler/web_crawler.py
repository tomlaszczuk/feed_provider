import json
import requests
from config import Config

from app.models import Offer, Photo, Product, SKU


class WebCrawler:
    def __init__(self, segment):
        self.segment = segment

    def offer_list(self):
        r = requests.post(Config.DEVICE_LIST,
                          data={"processSegmentationCode": self.segment})
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
        devices_json = r.json()
        return devices_json["devices"]
