from flask import Flask
from config import Config
from app.extensions import db, login_manager
from payment.yoomoney import yoomoney
import os


def create_app():
    app = Flask(__name__,template_folder='../templates',static_folder='../static')
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице'
    login_manager.login_message_category = 'info'

    #создаю рекламу
    try:
        from app.ads import AdsManager
        if app.config.get('ADS_CONFIG', {}).get('enabled', False):
            ads_manager = AdsManager(app)

            @app.context_processor
            def inject_ads():
                return {
                    'show_ad': ads_manager.show_ad,
                    'ad_scripts': ads_manager.get_all_scripts()
                }
    except ImportError as e:
        print(f"Рекламный модуль не загружен: {e}")

        #остальные инициализации
    yoomoney.init_app(app)

    #главные страницы(/, /bots, /create и тд)
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    #логин, регистрац., профиль
    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    #вебхуки, оплата, чекаути оплаты
    from payment import payment_bp
    app.register_blueprint(payment_bp)

    #создание папок
    os.makedirs(app.config['BOTS_DIR'], exist_ok=True)

    return app

#для
@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))