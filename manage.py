import os
from flask.ext.script import Manager, Server

from app import app
from config import config

app.config.from_object(config[os.getenv('FLASK_CONFIG') or 'default'])

manager = Manager(app)


if __name__ == "__main__":
    manager.run()