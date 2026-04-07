from typing import List, Dict
from datetime import datetime, timedelta


def get_dates_keyboard(days: int = 7) -> List[List[Dict]]:
    buttons = []
    today = datetime.now()

    for i in range(days):
        date = today + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        display_str = date.strftime("%d.%m (%a)")
        buttons.append([{
            'text': display_str,
            'data': f"date_{date_str}"
        }])
    buttons.append([{'text': "⬅️ Назад", 'data': "back_to_masters"}])
    return buttons

def get_times_keyboard(times: List[str]) -> List[List[Dict]]:
    buttons = []
    for time in times:
        buttons.append([{
            'text': time,
            'data': f"time_{time}"
        }])
    buttons.append([{'text': "⬅️ Назад", 'data': "back_to_dates"}])
    return buttons