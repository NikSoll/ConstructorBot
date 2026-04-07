from typing import Dict, Any, List
from datetime import datetime
from .base import BaseDatabase


class QuizDatabase(BaseDatabase):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, sheet_name="Результаты квизов")
        self._ensure_headers([
            "Дата", "ID пользователя", "Название квиза",
            "Оценка", "Результат"
        ])

    def save(self, data: Dict) -> bool:
        user_id = data.get('user_id', '')
        user_link = f"https://vk.com/id{user_id}" if user_id else ''

        total_score = data.get('total_score', 0)

        row = [
            data.get('date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            user_link,
            data.get('quiz_name', ''),
            data.get('result', ''),
            total_score
        ]
        return self.append_row(row)

    def save_result(self, result_data: Dict) -> bool:
        return self.save(result_data)

    def get_user_results(self, user_id: int) -> List[Dict]:
        user_link = f"https://vk.com/id{user_id}"
        return self.find_rows('Ссылка', user_link)