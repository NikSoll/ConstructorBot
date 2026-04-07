from typing import Dict, Any, List
from datetime import datetime
from .base import BaseDatabase


class MakeDatabase(BaseDatabase):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, sheet_name="Записи")#Тут название листа
        self._ensure_headers([#заголовки таблицы
            "Дата создания", "ID пользователя", "Имя заказчика(для самостоятельного заполнения)",
            "Имя", "Телефон", "Услуга", "Мастер", "Дата визита", "Время",
            "Комментарий", "Статус"
        ])

    def save(self, data: Dict) -> bool:
        user_id = data.get('user_id', '')
        user_link = f"https://vk.com/id{user_id}" if user_id else ''

        row = [
            data.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            user_link,
            data.get('username', ''),
            data.get('name', ''),
            data.get('phone', ''),
            data.get('service', ''),
            data.get('master', ''),
            data.get('date', ''),
            data.get('time', ''),
            data.get('comment', ''),
            'новая'
        ]
        return self.append_row(row)

    def add_booking(self, booking_data: Dict) -> bool:
        return self.save(booking_data)

    def get_user_bookings(self, user_id: int) -> List[Dict]:
        return self.find_rows('ID пользователя', str(user_id))

    def get_today_bookings(self) -> List[Dict]:
        today = datetime.now().strftime("%Y-%m-%d")
        records = self.get_all_records()

        result = []
        for record in records:
            record_date = str(record.get('Дата визита', ''))
            if today in record_date:
                result.append(record)

        return result