import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    #фласк
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

    #бд
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///bots.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    #пути
    BOTS_DIR = os.path.join(os.path.dirname(__file__), 'bots', 'generated')
    TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'bots', 'templates')

    #редиска
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    #гугл
    GOOGLE_CREDS_FILE = os.getenv('GOOGLE_CREDS_FILE', 'creds.json')

    #тест юмани
    YOOMONEY_TEST_MODE = os.getenv('YOOMONEY_TEST_MODE', 'True') == 'True'

    YOOMONEY_SHOP_ID = os.getenv('YOOMONEY_SHOP_ID', 'test_shop_id')
    YOOMONEY_SECRET_KEY = os.getenv('YOOMONEY_SECRET_KEY', 'test_secret_key')
    YOOMONEY_RETURN_URL = os.getenv('YOOMONEY_RETURN_URL', 'http://localhost:5000/payment/success')
    YOOMONEY_WEBHOOK_URL = os.getenv('YOOMONEY_WEBHOOK_URL', 'http://localhost:5000/payment/webhook/yoomoney')

    #реклама
    ADS_CONFIG = {
        'enabled': True,
        'show_placeholder': True,

        #Яндекс.Реклама (главная)
        'yandex': {
            'enabled': False,  #надо включить после получения  ID
            'block_id': '',  # ID блока из Яндекс.Рекламы
            'placement_id': '',
            'types': {
                'default': 'floorAd',
                'header': 'floorAd',
                'footer': 'floorAd'
            }
        },

        # VK Ads (доп)
        'vk_ads': {
            'enabled': False,
            'placement_id': ''
        },

        # MediaSniper (либо)
        'mediasniper': {
            'enabled': False,
            'zone_id': ''
        },

        'positions': {
            'header': {'enabled': True},
            'footer': {'enabled': True}
        }
    }