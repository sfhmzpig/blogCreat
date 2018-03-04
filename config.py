#! python3
class Config(object):
      pass
      SECRET_KEY='b2ec62de5310d2d4714d859074b64f82'
class ProdConfig(Config):
      pass
class DevConfig(Config):
      DEBUG=True
      SQLALCHEMY_DATABASE_URI="sqlite:///database.db"

