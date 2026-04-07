from typing import Dict, Any, List
from datetime import datetime
import json
from .base import BaseDatabase


class SurveyDatabase(BaseDatabase):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, sheet_name="Результаты опросов")
        self._ensure_headers([
            "Дата", "Ссылка", "Имя заказчика(для самостоятельного заполнения)",
            "Название опроса", "Ответы (JSON)"
        ])

    def save(self, data: Dict) -> bool:
        user_id = data.get('user_id', '')
        user_link = f"https://vk.com/id{user_id}" if user_id else ''

        answers_json = json.dumps(
            data.get('answers', []),
            ensure_ascii=False,
            indent=2
        )

        row = [
            data.get('date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            user_link,
            data.get('username', ''),
            data.get('survey_name', ''),
            answers_json
        ]
        return self.append_row(row)

    def save_survey_result(self, survey_data: Dict) -> bool:
        return self.save(survey_data)

    def get_user_surveys(self, user_id: int) -> List[Dict]:
        return self.find_rows('ID пользователя', str(user_id))