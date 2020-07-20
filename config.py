import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ThisIsTheSecretKey')

    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    APP_BASE_URL = os.environ['APP_BASE_URL']

    SWAGGER_BASE_URL = APP_BASE_URL

    AUTH0_CLIENT_ID = "BEPLKGgYmTMma3QUvs21cPY0Hq36ZAPP"
    AUTH0_CLIENT_SECRET = os.environ['AUTH0_CLIENT_SECRET']
    AUTH0_API_BASE_URL = "https://erigre.eu.auth0.com"
    AUTH0_ACCESS_TOKEN_URL = AUTH0_API_BASE_URL + '/oauth/token'
    AUTH0_AUTHORIZE_URL = AUTH0_API_BASE_URL + '/authorize'
    AUTH0_AUDIENCE = "trade_compliance_monitor"
    AUTH0_CALLBACK_URL = APP_BASE_URL + '/callback'



class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
