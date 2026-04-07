from abc import ABC, abstractmethod
import gspread
from google.oauth2.service_account import Credentials #афторизация
from typing import Dict, Any, Optional, List
import logging
import os


class BaseDatabase(ABC):
    def __init__(self, config: Dict[str, Any], sheet_name: str = "Sheet1"):
        self.config = config
        self.sheet_name = sheet_name #название листа
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = None
        self.sheet = None
        self._connect()

#подключение к таблице
    def _connect(self):
        try:
            creds_file = self.config.get('creds_file', 'creds.json')
            config_path = self.config.get('_config_path', '.')
            creds_path = os.path.join(config_path, creds_file)

            if not os.path.exists(creds_path):
                self.logger.warning(f"Файл учетных данных {creds_file} не найден в {creds_path}")
                return

            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]

            creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
            self.client = gspread.authorize(creds)
            sheet_url = self.config.get('sheet_url')
            if sheet_url:
                spreadsheet = self.client.open_by_url(sheet_url)
                self.sheet = spreadsheet.worksheet(self.sheet_name)
                self.logger.info(f"Подключение к Google Sheets: {spreadsheet.title}")
            else:
                self.logger.warning("URL таблицы не указан")

        except Exception as e:
            self.logger.error(f"Ошибка подключения: {e}")
            self.sheet = None

    def _ensure_connection(self):
        if not self.sheet:
            self._connect()
        return self.sheet is not None

    def _get_headers(self) -> List[str]:
        if not self._ensure_connection():
            return []

        try:
            return self.sheet.row_values(1)
        except Exception as e:
            self.logger.error(f"Ошибка получения заголовков: {e}")
            return []
#валид на нужные заголовки
    def _ensure_headers(self, required_headers: List[str]):
        if not self._ensure_connection():
            return False

        try:
            current_headers = self.sheet.row_values(1)
            if not current_headers:
                self.sheet.append_row(required_headers)
                return True

            missing = [h for h in required_headers if h not in current_headers]
            if missing:
                self.logger.warning(f"Отсутствуют заголовки: {missing}")

            return True
        except Exception as e:
            self.logger.error(f"Ошибка проверки заголовков: {e}")
            return False

#добавить строку в конец
    def append_row(self, row_data: List[Any]) -> bool:
        if not self._ensure_connection():
            return False

        try:
            self.sheet.append_row(row_data)
            return True
        except Exception as e:
            self.logger.error(f"Ошибка добавления строки: {e}")
            return False

#получить все записи
    def get_all_records(self) -> List[Dict]:
        if not self._ensure_connection():
            return []

        try:
            return self.sheet.get_all_records()
        except Exception as e:
            self.logger.error(f"Ошибка получения записей: {e}")
            return []

#поиск строк по знач
    def find_rows(self, column: str, value: str) -> List[Dict]:
        records = self.get_all_records()
        if not records:
            return []

        result = []
        for record in records:
            record_value = str(record.get(column, ''))
            if record_value == str(value):
                result.append(record)

        return result

#для дочерних классов
    @abstractmethod
    def save(self, data: Dict) -> bool:
        pass