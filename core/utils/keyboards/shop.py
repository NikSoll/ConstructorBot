from typing import List, Dict, Optional

def get_categories_keyboard(categories: List[Dict]) -> List[List[Dict]]:
    buttons = []
    for cat in categories:
        buttons.append([{
            'text': f"{cat['emoji']} {cat['name']}",
            'data': f"cat_{cat['id']}"
        }])
    buttons.append([{'text': "🛒 Корзина", 'data': "view_cart"}])
    return buttons

def get_products_keyboard(category_id: int, products: List[Dict], currency: str = "₽") -> List[List[Dict]]:
    buttons = []
    category_products = [p for p in products if p['category_id'] == category_id]
    for product in category_products:
        buttons.append([{
            'text': f"{product['name']} - {product['price']}{currency}",
            'data': f"prod_{product['id']}"
        }])
    buttons.append([{'text': "🔙 К категориям", 'data': "back_to_categories"}])
    return buttons

def get_product_detail_keyboard(product_id: int) -> List[List[Dict]]:
    return [
        [{'text': "➕ Добавить в корзину", 'data': f"add_{product_id}"}],
        [{'text': "🔙 К товарам", 'data': "back_to_products"}]
    ]

def get_cart_keyboard() -> List[List[Dict]]:
    return [
        [{'text': "✅ Оформить заказ", 'data': "checkout"}],
        [{'text': "🗑 Очистить корзину", 'data': "clear_cart"}],
        [{'text': "🛍 Продолжить покупки", 'data': "back_to_categories"}]
    ]