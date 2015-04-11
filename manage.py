#!/usr/bin/env python

import os
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand
from app import app, db, models
from config import config

app.config.from_object(config[os.getenv("FLASK_CONFIG") or "default"])

manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, Product=models.Product, SKU=models.SKU,
                Offer=models.Offer)

manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command("db", MigrateCommand)


if __name__ == "__main__":
    manager.run()