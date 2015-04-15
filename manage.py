#!/usr/bin/env python

import os
from timeit import default_timer as timer

from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand

from app import app, db, models
from config import config
from crawler.web_crawler import WebCrawler

app.config.from_object(config[os.getenv("FLASK_CONFIG") or "default"])

manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, Product=models.Product, SKU=models.SKU,
                Offer=models.Offer, Photo=models.Photo)

manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command("db", MigrateCommand)


@manager.command
def test():
    """Run unit tests"""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def dev_crawl():
    """Mini crawl for one process used to populate dev database"""
    start = timer()
    crawler = WebCrawler("IND.NEW.POSTPAID.MNP")
    offers = crawler.offer_list()
    for offer in offers:
        pages = crawler.pages(offer)
        for i in range(pages):
            devices = crawler.gather_devices(offer, i+1)
            for device in devices:
                crawler.save_or_update_device(device, offer)
    crawler.save_or_update_skus()
    crawler.save_request_counter()
    end = timer()
    print("It took %f seconds" % (end-start))


if __name__ == "__main__":
    manager.run()