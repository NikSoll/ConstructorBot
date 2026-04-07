import uuid
import json
import logging
from datetime import datetime
from yookassa import Configuration, Payment as YooPayment
from yookassa.domain.notification import WebhookNotification

from flask import current_app, url_for


class YooMoneyClient:
    def __init__(self, app=None):
        self.logger = logging.getLogger(__name__)
        if app:
            self.init_app(app)

    def init_app(self, app):
            if app.config.get('YOOMONEY_TEST_MODE', True):
                #тест режим
                Configuration.account_id = 'test_shop_id'
                Configuration.secret_key = 'test_secret_key'
                Configuration.api_endpoint = 'https://api.yookassa.ru/v3'  #тест URL
            else:
                Configuration.account_id = app.config['YOOMONEY_SHOP_ID']
                Configuration.secret_key = app.config['YOOMONEY_SECRET_KEY']

            self.return_url = app.config['YOOMONEY_RETURN_URL']
            self.webhook_url = app.config['YOOMONEY_WEBHOOK_URL']

    def create_payment(self, amount, description, metadata=None):
        try:
            import uuid
            from yookassa import Payment as YooPayment

            idempotence_key = str(uuid.uuid4())
            self.logger.info(f"Создание платежа на сумму {amount}, описание: {description}")

            payment_data = {
                "amount": {
                    "value": f"{amount:.2f}",
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": self.return_url
                },
                "capture": True,
                "description": description,
                "metadata": metadata or {}
            }

            self.logger.info(f"Данные платежа подготовлены, вызов YooPayment.create с ключом: {idempotence_key}")
            self.logger.info(f"Данные платежа: {payment_data}")

            # разделим создание на два шага для лучшей отладки
            payment = YooPayment.create(payment_data, idempotence_key)

            self.logger.info(f"Платеж успешно создан: {payment.id}")
            self.logger.info(f"Статус платежа: {payment.status}")
            self.logger.info(f"Подтверждение платежа: {payment.confirmation}")

            if payment.confirmation:
                self.logger.info(f"URL для подтверждения: {payment.confirmation.confirmation_url}")
            else:
                self.logger.warning("Нет подтверждения в ответе платежа!")

            return payment

        except Exception as e:
            self.logger.error(f"Ошибка при создании платежа: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_payment(self, payment_id):
        try:
            return YooPayment.find_one(payment_id)
        except Exception as e:
            self.logger.error(f"Ошибка при получении платежа: {e}")
            return None

    def process_webhook(self, request_json):
        try:
            notification = WebhookNotification(request_json)
            payment = notification.object

            self.logger.info(f"Получен webhook для платежа {payment.id}")

            return {
                'payment_id': payment.id,
                'status': payment.status,
                'metadata': payment.metadata,
                'amount': payment.amount.value
            }

        except Exception as e:
            self.logger.error(f"Ошибка при обработке webhook: {e}")
            return None


yoomoney = YooMoneyClient()