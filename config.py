import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'T0pS3Cr3T'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    DEVICE_LIST = "http://www.plus.pl/telefony/nowy-numer?" \
                  "p_p_id=deviceslistportlet_WAR_frontend_INSTANCE_4rYi&" \
                  "p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&" \
                  "p_p_resource_id=ajaxCall&p_p_cacheability=cacheLevelPage&" \
                  "p_p_col_id=column-1&p_p_col_pos=1&p_p_col_count=2"
    DEVICE_PRICES = "http://www.plus.pl/telefon?p_p_id=ajaxportlet_WAR_" \
                    "frontend_INSTANCE_T3lq&p_p_lifecycle=2&" \
                    "p_p_resource_id=devicesPrices"
    DEVICE_AVAILABLE = "http://www.plus.pl/telefon?p_p_id=ajaxportlet_WAR_" \
                       "frontend_INSTANCE_T3lq&p_p_lifecycle=2&p_p_resource_" \
                       "id=deviceAvailable"

    SEGMENTS = [
        "IND.NEW.POSTPAID.ACQ",
        "IND.NEW.POSTPAID.MNP",
        "IND.NEW.MIX.ACQ",
        "IND.SUB.MIG.POSTPAID",
        "IND.SUB.MIG.MIX",
        "SOHO.NEW.POSTPAID.ACQ",
        "SOHO.NEW.POSTPAID.MNP"
    ]

    def init_app(self):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'dev_database.sqlite3')


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'test_database.sqlite3')


config = {
    'development': DevelopmentConfig,
    'testing': TestConfig,

    'default': DevelopmentConfig
}