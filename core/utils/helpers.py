from typing import Dict, Any, Optional, List
from datetime import datetime
import re

#переводит 2026-04-02 в 02.04.2026
def format_date(date_str: str) -> str:
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d.%m.%Y")
    except:
        return date_str

#мастер по айди
def get_master_by_id(master_id: int, masters: List[Dict]) -> Optional[Dict]:
    return next((m for m in masters if m["id"] == master_id), None)

#продукт по айди
def get_product_by_id(product_id: int, products: List[Dict]) -> Optional[Dict]:
    return next((p for p in products if p["id"] == product_id), None)

#ката по айди
def get_category_by_id(category_id: int, categories: List[Dict]) -> Optional[Dict]:
    return next((c for c in categories if c["id"] == category_id), None)

#квиз по айди
def get_quiz_by_id(quiz_id: int, quizzes: List[Dict]) -> Optional[Dict]:
    return next((q for q in quizzes if q["id"] == quiz_id), None)

#опрос
def get_survey_by_id(survey_id: int, surveys: List[Dict]) -> Optional[Dict]:
    return next((s for s in surveys if s["id"] == survey_id), None)

#счет ссумы корзины
def calculate_total(cart: List[Dict]) -> int:
    return sum(item.get('price', 0) for item in cart)

#валидация телефона(доделать)
def validate_phone(phone: str) -> bool:
    digits = re.sub(r'\D', '', phone)
    return 10 <= len(digits) <= 15

#валид емыла(ну даже не валидация "@")
def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

#макс текст 100 длин
def truncate_text(text: str, max_length: int = 100) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."