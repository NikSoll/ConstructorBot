from typing import Dict, Any, List
from datetime import datetime
from .base import BaseDatabase


class ShopDatabase(BaseDatabase):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, sheet_name="Заказы")
        self._ensure_headers([
            "Дата создания", "ID пользователя", "Имя заказчика(для самостоятельного заполнения)",
            "Имя", "Телефон", "Адрес", "Комментарий",
            "Корзина", "Сумма", "Валюта", "Статус"
        ])

    def save(self, data: Dict) -> bool:
        user_id = data.get('user_id', '')
        user_link = f"https://vk.com/id{user_id}" if user_id else ''

        cart_lines = [
            f"{item['name']} - {item['price']}₽"
            for item in data.get('cart', [])
        ]
        cart_summary = "\n".join(cart_lines)

        row = [
            data.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            user_link,
            data.get('username', ''),
            data.get('name', ''),
            data.get('phone', ''),
            data.get('address', ''),
            data.get('comment', ''),
            cart_summary,
            data.get('total', 0),
            data.get('currency', '₽'),
            'новый'
        ]
        return self.append_row(row)

    def add_order(self, order_data: Dict) -> bool:
        return self.save(order_data)

    def get_user_orders(self, user_id: int) -> List[Dict]:
        return self.find_rows('ID пользователя', str(user_id))

    def get_today_orders(self) -> List[Dict]:
        today = datetime.now().strftime("%Y-%m-%d")
        records = self.get_all_records()

        result = []
        for record in records:
            created_at = str(record.get('Дата создания', ''))
            if today in created_at:
                result.append(record)

        return result