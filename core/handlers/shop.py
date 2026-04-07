from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from ..utils.helpers import get_product_by_id, get_category_by_id, calculate_total
from ..database.shop_db import ShopDatabase


class ShopHandlers:
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.db = ShopDatabase(self.config)
        self.logger = logging.getLogger(__name__)

        if not hasattr(self.bot, 'user_carts'):
            self.bot.user_carts = {}

    async def handle_start(self, user_id: int, username: str = "", full_name: str = "", args: list = None) -> Optional[Dict]:
        if user_id in self.bot.user_sessions:
            del self.bot.user_sessions[user_id]
        if user_id in self.bot.user_carts:
            del self.bot.user_carts[user_id]

        return {
            'text': self.config['messages']['welcome'].format(
                name=self.config['shop_settings']['name']
            ),
            'keyboard': self.bot.create_reply_keyboard([
                ["🛍 Каталог", "🛒 Корзина"],
                ["ℹ️ О магазине", "📞 Контакты"]
            ])
        }

    async def handle_message(self, user_id: int, text: str) -> Optional[Dict]:
        session = self.bot.user_sessions.get(user_id, {})
        state = session.get('state')

        if text == "🛍 Каталог":
            return await self._show_catalog(user_id)

        elif text == "🛒 Корзина":
            return await self._show_cart(user_id)

        elif text == "ℹ️ О магазине":
            return {
                'text': f"🛍 *О магазине {self.config['shop_settings']['name']}*\n\n"
                        "Мы предлагаем качественные товары по доступным ценам.\n"
                        "• Доставка по городу\n"
                        "• Оплата при получении\n"
                        "• Гарантия качества"
            }

        elif text == "📞 Контакты":
            return {
                'text': "📞 *Контакты*\n\n"
                        "📍 Адрес: г. Омск, ул. Масленникова, д. 45\n"
                        "🕐 Часы работы: 10:00 - 20:00\n"
                        "📞 Телефон: +7 (905) 190-01-54"
            }

        elif text == "❌ Отменить заказ":
            if user_id in self.bot.user_sessions:
                del self.bot.user_sessions[user_id]
            return {
                'text': "❌ Оформление заказа отменено",
                'keyboard': self.bot.create_reply_keyboard([
                    ["🛍 Каталог", "🛒 Корзина"],
                    ["ℹ️ О магазине", "📞 Контакты"]
                ])
            }

        if state == 'entering_name':
            return await self._process_name(user_id, text)

        elif state == 'entering_phone':
            return await self._process_phone(user_id, text)

        elif state == 'entering_address':
            return await self._process_address(user_id, text)

        elif state == 'entering_comment':
            return await self._process_comment(user_id, text)

        return None

    async def handle_callback(self, user_id: int, callback_data: str) -> Optional[Dict]:
        self.logger.info(f"Магазин callback от {user_id}: {callback_data}")

        if user_id not in self.bot.user_sessions:
            self.bot.user_sessions[user_id] = {}


        if callback_data.startswith('cat_'):
            return await self._show_category(user_id, callback_data)

        elif callback_data.startswith('prod_'):
            return await self._show_product(user_id, callback_data)

        elif callback_data.startswith('add_'):
            return await self._add_to_cart(user_id, callback_data)

        elif callback_data == 'view_cart':
            return await self._show_cart(user_id, callback=True)

        elif callback_data == 'clear_cart':
            return await self._clear_cart(user_id)

        elif callback_data == 'checkout':
            return await self._start_checkout(user_id)

        elif callback_data == 'back_to_categories':
            return await self._show_catalog(user_id, callback=True)

        elif callback_data == 'back_to_products':
            return await self._back_to_products(user_id)

        return None

    async def _show_catalog(self, user_id: int, callback: bool = False) -> Dict:
        if user_id not in self.bot.user_sessions:
            self.bot.user_sessions[user_id] = {}

        self.bot.user_sessions[user_id]['state'] = 'browsing'

        buttons = []
        row = []
        for cat in self.config['categories']:
            row.append({
                'text': f"{cat['emoji']} {cat['name']}",
                'data': f"cat_{cat['id']}"
            })
            if len(row) == 3:
                buttons.append(row)
                row = []

        if row:
            buttons.append(row)

        buttons.append([{'text': "🛒 Корзина", 'data': "view_cart"}])
        return {
            'text': self.config['messages']['catalog'],
            'keyboard': self.bot.create_inline_keyboard(buttons),
            'edit': callback
        }

    async def _show_category(self, user_id: int, callback_data: str) -> Optional[Dict]:
        category_id = int(callback_data.split('_')[1])
        category = get_category_by_id(category_id, self.config['categories'])

        if not category:
            return None

        self.bot.user_sessions[user_id]['current_category'] = category_id
        self.bot.user_sessions[user_id]['state'] = 'browsing'

        category_products = [
            p for p in self.config['products']
            if p['category_id'] == category_id
        ]

        buttons = []
        row = []
        for product in category_products:
            row.append({
                'text': f"{product['name']} - {product['price']}{self.config['shop_settings']['currency']}",
                'data': f"prod_{product['id']}"
            })
            if len(row) == 2:  # По 2 товара в ряду
                buttons.append(row)
                row = []

        if row:
            buttons.append(row)

        buttons.append([{'text': "🔙 К категориям", 'data': "back_to_categories"}])

        return {
            'text': f"📁 *{category['emoji']} {category['name']}*\n\nВыберите товар:",
            'keyboard': self.bot.create_inline_keyboard(buttons)
        }

    async def _show_product(self, user_id: int, callback_data: str) -> Optional[Dict]:
        product_id = int(callback_data.split('_')[1])
        product = get_product_by_id(product_id, self.config['products'])

        if not product:
            return None

        self.bot.user_sessions[user_id]['current_product'] = product_id
        self.bot.user_sessions[user_id]['state'] = 'viewing_product'

        text = self.config['messages']['product_info'].format(
            name=product['name'],
            price=product['price'],
            currency=self.config['shop_settings']['currency'],
            desc=product['desc']
        )

        buttons = [
            [{'text': "➕ Добавить в корзину", 'data': f"add_{product_id}"}],
            [{'text': "🔙 К товарам", 'data': "back_to_products"}]
        ]

        if product.get('photo'):
            await self.bot.send_photo(
                user_id,
                product['photo'],
                caption=text,
                keyboard=self.bot.create_inline_keyboard(buttons)
            )
            return None
        else:
            return {
                'text': text,
                'keyboard': self.bot.create_inline_keyboard(buttons)
            }

    async def _add_to_cart(self, user_id: int, callback_data: str) -> Optional[Dict]:
        product_id = int(callback_data.split('_')[1])
        product = get_product_by_id(product_id, self.config['products'])

        if not product:
            return None

        cart = self.bot.user_carts.get(user_id, [])

        cart.append({
            'id': product['id'],
            'name': product['name'],
            'price': product['price']
        })

        self.bot.user_carts[user_id] = cart

        category_id = self.bot.user_sessions[user_id].get('current_category')
        if category_id:
            return await self._show_category(
                user_id,
                f"cat_{category_id}"
            )

        return None

    async def _show_cart(self, user_id: int, callback: bool = False) -> Dict:
        cart = self.bot.user_carts.get(user_id, [])

        if not cart:
            return {
                'text': self.config['messages']['cart_empty'],
                'edit': callback
            }

        total = calculate_total(cart)

        cart_lines = []
        for i, item in enumerate(cart, 1):
            cart_lines.append(f"{i}. {item['name']} - {item['price']}₽")
        cart_text = "\n".join(cart_lines)

        text = self.config['messages']['cart'].format(
            cart=cart_text,
            total=total,
            currency=self.config['shop_settings']['currency']
        )

        buttons = [
            [{'text': "✅ Оформить заказ", 'data': "checkout"}],
            [{'text': "🗑 Очистить корзину", 'data': "clear_cart"}],
            [{'text': "🛍 Продолжить покупки", 'data': "back_to_categories"}]
        ]

        self.bot.user_sessions[user_id]['state'] = 'in_cart'

        return {
            'text': text,
            'keyboard': self.bot.create_inline_keyboard(buttons),
            'edit': callback
        }

    async def _clear_cart(self, user_id: int) -> Dict:
        if user_id in self.bot.user_carts:
            del self.bot.user_carts[user_id]

        return {
            'text': "🗑 *Корзина очищена*",
            'edit': True
        }

    async def _start_checkout(self, user_id: int) -> Optional[Dict]:
        cart = self.bot.user_carts.get(user_id, [])

        if not cart:
            return {
                'text': "Корзина пуста!",
                'edit': True
            }

        self.bot.user_sessions[user_id]['state'] = 'entering_name'

        return {
            'text': self.config['messages']['ask_name'],
            'edit': True
        }

    async def _process_name(self, user_id: int, text: str) -> Dict:
        self.bot.user_sessions[user_id]['customer_name'] = text
        self.bot.user_sessions[user_id]['state'] = 'entering_phone'

        return {
            'text': self.config['messages']['ask_phone'],
            'keyboard': self.bot.create_reply_keyboard([["❌ Отменить заказ"]])
        }

    async def _process_phone(self, user_id: int, text: str) -> Dict:
        self.bot.user_sessions[user_id]['customer_phone'] = text
        self.bot.user_sessions[user_id]['state'] = 'entering_address'

        return {
            'text': self.config['messages']['ask_address']
        }

    async def _process_address(self, user_id: int, text: str) -> Dict:
        self.bot.user_sessions[user_id]['customer_address'] = text
        self.bot.user_sessions[user_id]['state'] = 'entering_comment'

        return {
            'text': "💬 *Добавьте комментарий к заказу (если нужно):*\n"
                    "Или отправьте '-'"
        }

    async def _process_comment(self, user_id: int, text: str) -> Dict:
        comment = text if text != "-" else ""

        data = self.bot.user_sessions.get(user_id, {})
        cart = self.bot.user_carts.get(user_id, [])

        order = {
            'user_id': user_id,
            'username': data.get('username', ''),
            'name': data.get('customer_name'),
            'phone': data.get('customer_phone'),
            'address': data.get('customer_address'),
            'comment': comment,
            'cart': cart.copy(),
            'total': calculate_total(cart),
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        self.db.add_order(order)

        cart_lines = []
        for i, item in enumerate(cart, 1):
            cart_lines.append(f"{i}. {item['name']} - {item['price']}₽")
        cart_text = "\n".join(cart_lines)

        order_details = (
            f"*Ваш заказ:*\n{cart_text}\n"
            f"💰 *Итого: {order['total']}{self.config['shop_settings']['currency']}*\n\n"
            f"📞 *Телефон:* {order['phone']}\n"
            f"📍 *Адрес:* {order['address']}"
        )

        if user_id in self.bot.user_carts:
            del self.bot.user_carts[user_id]
        if user_id in self.bot.user_sessions:
            del self.bot.user_sessions[user_id]

        if self.config['shop_settings'].get('admin_chat_id'):
            admin_text = f"🛍 *Новый заказ!*\n\n{order_details}"
            await self.bot.notify_admin(admin_text)

        return {
            'text': self.config['messages']['order_success'].format(
                order_details=order_details
            ),
            'keyboard': self.bot.create_reply_keyboard([
                ["🛍 Каталог", "🛒 Корзина"],
                ["ℹ️ О магазине", "📞 Контакты"]
            ])
        }

    async def _back_to_products(self, user_id: int) -> Optional[Dict]:
        category_id = self.bot.user_sessions[user_id].get('current_category')
        if category_id:
            return await self._show_category(
                user_id,
                f"cat_{category_id}"
            )

        return await self._show_catalog(user_id, callback=True)