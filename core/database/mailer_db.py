import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials


class MailerDatabase:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.subscribers_sheet = None
        self.mailings_sheet = None
        self.history_sheet = None
        self.spreadsheet = None
        self._connect_with_sheets()

    def _connect_with_sheets(self):
        try:
            creds_file = self.config.get('creds_file', 'creds.json')
            config_path = self.config.get('_config_path', '.')
            creds_path = os.path.join(config_path, creds_file)
            sheet_url = self.config.get('sheet_url')

            if not os.path.exists(creds_path):
                self.logger.warning(f"Файл учетных данных {creds_file} не найден")
                return

            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
            client = gspread.authorize(creds)

            if not sheet_url:
                self.logger.warning("URL таблицы не указан")
                return

            self.spreadsheet = client.open_by_url(sheet_url)

            try:
                self.subscribers_sheet = self.spreadsheet.worksheet("Подписчики")
            except:
                self.subscribers_sheet = self.spreadsheet.add_worksheet("Подписчики", 1000, 20)
                self.subscribers_sheet.append_row(["Дата подписки", "Название рассылки", "Ссылка на пользователя"])

            try:
                self.mailings_sheet = self.spreadsheet.worksheet("Рассылки")
            except:
                self.mailings_sheet = self.spreadsheet.add_worksheet("Рассылки", 100, 20)
                self.mailings_sheet.append_row(["Дата создания", "Название", "Описание"])

            try:
                self.history_sheet = self.spreadsheet.worksheet("История рассылок")
            except:
                self.history_sheet = self.spreadsheet.add_worksheet("История рассылок", 1000, 10)
                self.history_sheet.append_row(["Дата", "Рассылка", "Текст", "Всего", "Отправлено", "Ошибок"])

            self.logger.info(f"Подключение к Google Sheets")

        except Exception as e:
            self.logger.error(f"Ошибка подключения: {e}")

    def get_mailings(self) -> List[Dict]:
        if not self.mailings_sheet:
            return []

        try:
            records = self.mailings_sheet.get_all_records()
            result = []
            for i, record in enumerate(records, start=2):
                result.append({
                    'ID': i,
                    'Дата создания': record.get('Дата создания', ''),
                    'Название': record.get('Название', ''),
                    'Описание': record.get('Описание', '')
                })
            return result
        except Exception as e:
            self.logger.error(f"Ошибка получения рассылок: {e}")
            return []

    def add_mailing(self, name: str, description: str) -> Optional[int]:
        if not self.mailings_sheet:
            return None

        try:
            records = self.mailings_sheet.get_all_records()
            next_id = len(records) + 2  #потому что первая строка заголовок

            row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), name, description]
            self.mailings_sheet.append_row(row)
            return next_id
        except Exception as e:
            self.logger.error(f"Ошибка добавления рассылки: {e}")
            return None

    def delete_mailing(self, mailing_id: int) -> bool:
        if not self.mailings_sheet:
            return False

        try:
            self.mailings_sheet.delete_rows(mailing_id)

            if self.subscribers_sheet:
                sub_records = self.subscribers_sheet.get_all_records()
                rows_to_delete = []
                for i, record in enumerate(sub_records, start=2):
                    if str(record.get('Рассылка', '')) == str(mailing_id):
                        rows_to_delete.append(i)
                for row in reversed(rows_to_delete):
                    self.subscribers_sheet.delete_rows(row)

            return True
        except Exception as e:
            self.logger.error(f"Ошибка удаления рассылки: {e}")
            return False

    def subscribe(self, user_id: int, mailing_id: int, user_link: str, mailing_name: str) -> bool:
        if not self.subscribers_sheet:
            return False

        try:
            if self.is_subscribed(user_link, mailing_name):
                return False

            row = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                mailing_name,
                user_link
            ]
            self.subscribers_sheet.append_row(row)
            return True
        except Exception as e:
            self.logger.error(f"Ошибка подписки: {e}")
            return False

    def unsubscribe(self, user_link: str, mailing_name: str) -> bool:
        if not self.subscribers_sheet:
            return False

        try:
            records = self.subscribers_sheet.get_all_records()
            for i, record in enumerate(records, start=2):
                if str(record.get('Ссылка на пользователя', '')) == str(user_link) and \
                        str(record.get('Название рассылки', '')) == str(mailing_name):
                    self.subscribers_sheet.delete_rows(i)
                    return True
        except Exception as e:
            self.logger.error(f"Ошибка отписки: {e}")
        return False

    def is_subscribed(self, user_link: str, mailing_name: str) -> bool:
        if not self.subscribers_sheet:
            return False

        try:
            records = self.subscribers_sheet.get_all_records()
            for record in records:
                if str(record.get('Ссылка на пользователя', '')) == str(user_link) and \
                        str(record.get('Название рассылки', '')) == str(mailing_name):
                    return True
        except Exception as e:
            self.logger.error(f"Ошибка проверки подписки: {e}")
        return False

    def get_user_subscriptions(self, user_link: str) -> List[Dict]:
        if not self.subscribers_sheet:
            return []

        subscriptions = []
        try:
            records = self.subscribers_sheet.get_all_records()
            mailings = {m['Название']: m for m in self.get_mailings()}

            for record in records:
                if str(record.get('Ссылка на пользователя', '')) == str(user_link):
                    mailing_name = record.get('Название рассылки', '')
                    if mailing_name in mailings:
                        subscriptions.append(mailings[mailing_name])
        except Exception as e:
            self.logger.error(f"Ошибка получения подписок пользователя: {e}")
        return subscriptions

    def get_mailing_subscribers(self, mailing_name: str) -> List[str]:
        if not self.subscribers_sheet:
            return []

        subscribers = []
        try:
            records = self.subscribers_sheet.get_all_records()
            for record in records:
                if str(record.get('Название рассылки', '')) == str(mailing_name):
                    subscribers.append(record.get('Ссылка на пользователя', ''))
        except Exception as e:
            self.logger.error(f"Ошибка получения подписчиков рассылки: {e}")
        return subscribers

    def get_subscriber_count(self, mailing_name: str) -> int:
        return len(self.get_mailing_subscribers(mailing_name))

    def save_mailing_history(self, data: Dict) -> bool:
        if not self.history_sheet:
            self.logger.warning("Лист истории недоступен")
            return False

        try:
            row = [
                data.get('date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                data.get('group', ''),
                data.get('text', ''),
                data.get('total', 0),
                data.get('sent', 0),
                data.get('failed', 0)
            ]
            self.history_sheet.append_row(row)
            self.logger.info(f"Сохранена история рассылки: {data.get('group')}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка сохранения истории рассылки: {e}")
            return False