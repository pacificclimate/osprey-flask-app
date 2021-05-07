"""Flask configuration options"""


class Config(object):
    DEBUG = False
    TESTING = False


class ProdConfig(Config):
    pass


class DevConfig(Config):
    DEBUG = True


class TestConfig(Config):
    TESTING = True
