#гугл таблица
from .base import BaseDatabase
from .make_db import MakeDatabase
from .shop_db import ShopDatabase
from .quiz_db import QuizDatabase
from .survey_db import SurveyDatabase
from .mailer_db import MailerDatabase


def get_db_for_type(bot_type: str, config: dict):
    dbs = {
        'make': MakeDatabase,
        'shop': ShopDatabase,
        'quiz': QuizDatabase,
        'survey': SurveyDatabase,
        'mailer': MailerDatabase
    }
    db_class = dbs.get(bot_type)
    if db_class:
        return db_class(config)
    return None

__all__ = [
    'BaseDatabase',
    'MakeDatabase',
    'ShopDatabase',
    'QuizDatabase',
    'SurveyDatabase',
    'MailerDatabase',
    'get_db_for_type'
]