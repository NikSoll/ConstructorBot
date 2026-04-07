from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import asyncio

from ..database.mailer_db import MailerDatabase


class MailerHandlers:
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        db_config = self.config.copy()
        if '_config_path' not in db_config:
            db_config['_config_path'] = bot.config.get('_config_path', '.')
        self.db = MailerDatabase(db_config)
        self.logger = logging.getLogger(__name__)
        self.admin_id = self.config.get('admin_id')
        self.is_admin = False

    async def handle_start(self, user_id: int, username: str = "", full_name: str = "", args: list = None) -> Optional[Dict]:
        if user_id in self.bot.user_sessions:
            del self.bot.user_sessions[user_id]

        self.is_admin = str(user_id) == str(self.admin_id)

        if self.is_admin:
            return {
                'text': "👑 *Админ-панель рассыльщика*\n\nВыберите действие:",
                'keyboard': self.bot.create_reply_keyboard([
                    ["📊 Статистика", "📝 Управление рассылками"],
                    ["✉️ Отправить сообщение"]
                ])
            }
        else:
            return {
                'text': "📢 *Бот-рассыльщик*\n\nВыберите действие:",
                'keyboard': self.bot.create_reply_keyboard([
                    ["📋 Посмотреть рассылки", "📋 Мои рассылки"]
                ])
            }

    async def handle_message(self, user_id: int, text: str) -> Optional[Dict]:
        session = self.bot.user_sessions.get(user_id, {})
        state = session.get('state')

        if text == "📋 Посмотреть рассылки":
            return await self._show_mailings(user_id)
        elif text == "📋 Мои рассылки":
            return await self._show_my_subscriptions(user_id)
        elif text == "📊 Статистика":
            return await self._show_stats(user_id)
        elif text == "📝 Управление рассылками":
            return await self._manage_mailings(user_id)
        elif text == "✉️ Отправить сообщение":
            return await self._start_send_message(user_id)

        if state == 'choosing_mailing_for_send':
            return await self._process_mailing_for_send(user_id, text)
        elif state == 'entering_message_text':
            return await self._process_message_text(user_id, text)
        elif state == 'adding_mailing':
            return await self._process_add_mailing(user_id, text)

        return None

    async def handle_callback(self, user_id: int, callback_data: str) -> Optional[Dict]:

        if user_id not in self.bot.user_sessions:
            self.bot.user_sessions[user_id] = {}

        if callback_data.startswith('subscribe_'):
            mailing_id = int(callback_data.split('_')[1])
            return await self._subscribe_action(user_id, mailing_id)
        elif callback_data.startswith('unsubscribe_'):
            mailing_id = int(callback_data.split('_')[1])
            return await self._unsubscribe_action(user_id, mailing_id)
        elif callback_data.startswith('delete_mailing_'):
            mailing_id = int(callback_data.split('_')[2])
            return await self._delete_mailing_action(user_id, mailing_id)
        elif callback_data == 'add_mailing':
            return await self._add_mailing_form(user_id)
        elif callback_data == 'back_to_admin':
            self.bot.user_sessions.pop(user_id, None)
            return {
                'text': "👑 *Админ-панель рассыльщика*\n\nВыберите действие:",
                'keyboard': self.bot.create_reply_keyboard([
                    ["📊 Статистика", "📝 Управление рассылками"],
                    ["✉️ Отправить сообщение"]
                ])
            }
        elif callback_data.startswith('select_mailing_'):
            mailing_id = int(callback_data.split('_')[2])

            if user_id not in self.bot.user_sessions:
                self.bot.user_sessions[user_id] = {}

            self.bot.user_sessions[user_id]['selected_mailing'] = mailing_id
            self.bot.user_sessions[user_id]['state'] = 'entering_message_text'
            return {
                'text': "✏️ *Введите текст сообщения для рассылки:*\n\n"
                        "Вы можете отправить текст, а затем (опционально) фото.",
                'edit': True
            }
        elif callback_data == 'confirm_send':
            return await self._send_mailing(user_id)
        elif callback_data == 'cancel_send':
            self.bot.user_sessions.pop(user_id, None)
            return {
                'text': "❌ Отправка сообщения отменена",
                'keyboard': self.bot.create_reply_keyboard([
                    ["📊 Статистика", "📝 Управление рассылками"],
                    ["✉️ Отправить сообщение"]
                ]),
                'edit': True
            }

        return None

    async def _show_mailings(self, user_id: int) -> Dict:
        mailings = self.db.get_mailings()

        if not mailings:
            return {
                'text': "📭 Пока нет доступных рассылок.\n\nЗагляните позже!"
            }

        text = "📋 *Доступные рассылки:*\n\n"
        buttons = []

        for mailing in mailings:
            mailing_id = mailing.get('ID')
            name = mailing.get('Название', 'Без названия')
            desc = mailing.get('Описание', '')

            text += f"📌 *{name}*\n"
            if desc:
                text += f"   {desc}\n"
            text += f"   👥 Подписчиков: {self.db.get_subscriber_count(name)}\n\n"

            buttons.append([{
                'text': f"✅ Подписаться на {name}",
                'data': f"subscribe_{mailing_id}"
            }])

        return {
            'text': text,
            'keyboard': self.bot.create_inline_keyboard(buttons)
        }

    async def _show_my_subscriptions(self, user_id: int) -> Dict:
        user_link = await self._get_user_link(user_id)
        subscriptions = self.db.get_user_subscriptions(user_link)

        if not subscriptions:
            return {
                'text': "📭 Вы не подписаны ни на одну рассылку.\n\n"
                        "Нажмите «Посмотреть рассылки», чтобы подписаться."
            }

        text = "📋 *Ваши подписки:*\n\n"
        buttons = []

        for sub in subscriptions:
            mailing_id = sub.get('ID')
            name = sub.get('Название', 'Без названия')

            text += f"📌 *{name}*\n"
            text += f"   👥 Подписчиков: {self.db.get_subscriber_count(name)}\n\n"

            buttons.append([{
                'text': f"❌ Отписаться от {name}",
                'data': f"unsubscribe_{mailing_id}"
            }])

        return {
            'text': text,
            'keyboard': self.bot.create_inline_keyboard(buttons)
        }

    async def _subscribe_action(self, user_id: int, mailing_id: int) -> Dict:
        mailings = self.db.get_mailings()
        mailing = next((m for m in mailings if m.get('ID') == mailing_id), None)

        if not mailing:
            return {'text': "❌ Рассылка не найдена", 'edit': True}

        user_link = await self._get_user_link(user_id)
        mailing_name = mailing.get('Название', '')

        if self.db.subscribe(user_id, mailing_id, user_link, mailing_name):
            name = mailing.get('Название', 'рассылка')
            return {
                'text': f"✅ Вы подписались на рассылку *{name}*!",
                'edit': True
            }
        else:
            return {
                'text': f"ℹ️ Вы уже подписаны на эту рассылку",
                'edit': True
            }

    async def _unsubscribe_action(self, user_id: int, mailing_id: int) -> Dict:
        mailings = self.db.get_mailings()
        mailing = next((m for m in mailings if m.get('ID') == mailing_id), None)

        if not mailing:
            return {'text': "❌ Рассылка не найдена", 'edit': True}

        user_link = await self._get_user_link(user_id)
        mailing_name = mailing.get('Название', '')

        if self.db.unsubscribe(user_link, mailing_name):
            name = mailing.get('Название', 'рассылка')
            return {
                'text': f"❌ Вы отписались от рассылки *{name}*.",
                'edit': True
            }
        else:
            return {
                'text': f"ℹ️ Вы не были подписаны на эту рассылку",
                'edit': True
            }

    async def _show_stats(self, user_id: int) -> Optional[Dict]:
        if not self.is_admin:
            return {'text': "⛔️ Нет доступа"}

        mailings = self.db.get_mailings()

        if not mailings:
            return {
                'text': "📊 *Статистика*\n\nНет созданных рассылок.\n"
                        "Используйте «Управление рассылками» → «Добавить рассылку»"
            }

        text = "📊 *Статистика рассылок*\n\n"
        for mailing in mailings:
            name = mailing.get('Название', 'Без названия')
            count = self.db.get_subscriber_count(name)
            text += f"📌 *{name}* — 👥 {count} подписчиков\n"

        return {'text': text}

    async def _manage_mailings(self, user_id: int) -> Optional[Dict]:
        if not self.is_admin:
            return {'text': "⛔️ Нет доступа"}

        mailings = self.db.get_mailings()

        text = "📝 *Управление рассылками*\n\n"
        buttons = []

        for mailing in mailings:
            mailing_id = mailing.get('ID')
            name = mailing.get('Название', 'Без названия')
            count = self.db.get_subscriber_count(name)
            text += f"   👥 Подписчиков: {self.db.get_subscriber_count(name)}\n\n"
            buttons.append([{
                'text': f"🗑️ Удалить {name}",
                'data': f"delete_mailing_{mailing_id}"
            }])

        buttons.append([{'text': "➕ Добавить рассылку", 'data': "add_mailing"}])
        buttons.append([{'text': "◀️ Назад", 'data': "back_to_admin"}])

        return {
            'text': text,
            'keyboard': self.bot.create_inline_keyboard(buttons)
        }

    async def _add_mailing_form(self, user_id: int) -> Optional[Dict]:
        if not self.is_admin:
            return {'text': "⛔️ Нет доступа"}

        if user_id not in self.bot.user_sessions:
            self.bot.user_sessions[user_id] = {}

        self.bot.user_sessions[user_id]['state'] = 'adding_mailing'
        return {
            'text': "➕ *Добавление новой рассылки*\n\n"
                    "Введите название рассылки:",
            'edit': True
        }

    async def _process_add_mailing(self, user_id: int, text: str) -> Optional[Dict]:
        if not self.is_admin:
            return {'text': "⛔️ Нет доступа"}

        name = text.strip()
        if not name:
            return {
                'text': "❌ Название не может быть пустым. Попробуйте снова:",
                'edit': True
            }

        mailing_id = self.db.add_mailing(name, "")
        if mailing_id:
            if user_id in self.bot.user_sessions:
                self.bot.user_sessions.pop(user_id, None)
            return {
                'text': f"✅ Рассылка *{name}* успешно создана!",
                'keyboard': self.bot.create_reply_keyboard([
                    ["📊 Статистика", "📝 Управление рассылками"],
                    ["✉️ Отправить сообщение"]
                ]),
                'edit': True
            }
        else:
            return {
                'text': "❌ Ошибка при создании рассылки. Попробуйте позже.",
                'edit': True
            }

    async def _delete_mailing_action(self, user_id: int, mailing_id: int) -> Dict:
        if not self.is_admin:
            return {'text': "⛔️ Нет доступа", 'edit': True}

        if self.db.delete_mailing(mailing_id):
            return {
                'text': "✅ Рассылка удалена вместе со всеми подписчиками",
                'edit': True
            }
        else:
            return {
                'text': "❌ Ошибка при удалении рассылки",
                'edit': True
            }

    async def _start_send_message(self, user_id: int) -> Optional[Dict]:
        if not self.is_admin:
            return {'text': "⛔️ Нет доступа"}

        mailings = self.db.get_mailings()

        if not mailings:
            return {
                'text': "📭 Нет созданных рассылок.\n\n"
                        "Сначала добавьте рассылку в «Управление рассылками»."
            }

        text = "✉️ *Выберите рассылку для отправки сообщения:*\n\n"
        buttons = []

        for mailing in mailings:
            mailing_id = mailing.get('ID')
            name = mailing.get('Название', 'Без названия')
            count = self.db.get_subscriber_count(name)
            text += f"📌 *{name}* — 👥 {count} подписчиков\n"
            buttons.append([{
                'text': f"📨 {name}",
                'data': f"select_mailing_{mailing_id}"
            }])

        buttons.append([{'text': "◀️ Назад", 'data': "back_to_admin"}])

        if user_id not in self.bot.user_sessions:
            self.bot.user_sessions[user_id] = {}

        self.bot.user_sessions[user_id]['state'] = 'choosing_mailing_for_send'

        return {
            'text': text,
            'keyboard': self.bot.create_inline_keyboard(buttons)
        }

    async def _process_mailing_for_send(self, user_id: int, text: str) -> Optional[Dict]:
        return None

    async def _process_message_text(self, user_id: int, text: str) -> Optional[Dict]:
        if not self.is_admin:
            return {'text': "⛔️ Нет доступа"}

        if user_id not in self.bot.user_sessions:
            self.bot.user_sessions[user_id] = {}

        mailing_id = self.bot.user_sessions[user_id].get('selected_mailing')
        if not mailing_id:
            return {'text': "❌ Ошибка: рассылка не выбрана"}

        mailings = self.db.get_mailings()
        mailing = next((m for m in mailings if m.get('ID') == mailing_id), None)
        if not mailing:
            return {'text': "❌ Рассылка не найдена"}

        mailing_name = mailing.get('Название', '')
        subscribers = self.db.get_mailing_subscribers(mailing_name)

        if not subscribers:
            return {
                'text': f"⚠️ У рассылки *{mailing_name}* нет подписчиков.\n\n"
                        "Сообщение не отправлено."
            }

        self.bot.user_sessions[user_id]['message_text'] = text
        self.bot.user_sessions[user_id]['selected_mailing_name'] = mailing_name
        self.bot.user_sessions[user_id]['state'] = 'confirm_send'

        preview = f"📨 *Предпросмотр рассылки*\n\n"
        preview += f"📌 Рассылка: *{mailing_name}*\n"
        preview += f"👥 Получателей: *{len(subscribers)}*\n\n"
        preview += f"📝 *Текст:*\n{text}\n\n"
        preview += "Подтвердите отправку:"

        buttons = [
            [{'text': "✅ Отправить", 'data': "confirm_send"}],
            [{'text': "❌ Отмена", 'data': "cancel_send"}]
        ]

        return {
            'text': preview,
            'keyboard': self.bot.create_inline_keyboard(buttons)
        }

    async def _send_mailing(self, user_id: int) -> Optional[Dict]:
        if user_id not in self.bot.user_sessions:
            self.logger.error(f"Нет сессии для пользователя {user_id}")
            return {'text': "❌ Ошибка: сессия не найдена"}

        mailing_id = self.bot.user_sessions[user_id].get('selected_mailing')
        mailing_name = self.bot.user_sessions[user_id].get('selected_mailing_name')
        message_text = self.bot.user_sessions[user_id].get('message_text')

        if not mailing_id or not message_text or not mailing_name:
            self.logger.error("Отсутствуют необходимые данные")
            return {'text': "❌ Ошибка: данные не найдены"}

        mailings = self.db.get_mailings()
        mailing = next((m for m in mailings if m.get('ID') == mailing_id), None)
        if not mailing:
            self.logger.error(f"Рассылка не найдена: {mailing_id}")
            return {'text': "❌ Рассылка не найдена"}

        subscribers = self.db.get_mailing_subscribers(mailing_name)

        await self.bot.send_message(user_id, f"📨 Начинаю рассылку для {len(subscribers)} подписчиков...")

        sent = 0
        failed = 0

        for idx, user_link in enumerate(subscribers):
            try:

                target_user_id = self._extract_user_id_from_link(user_link)

                if target_user_id == 0:
                    self.logger.error(f"Неверная ссылка на пользователя: {user_link}")
                    failed += 1
                    continue

                result = await self.bot.send_message(target_user_id, f"📢 *{mailing_name}*\n\n{message_text}")
                sent += 1

            except Exception as e:
                failed += 1
                self.logger.error(f"Ошибка отправки для {user_link}: {e}", exc_info=True)

            await asyncio.sleep(0.05)

        self.db.save_mailing_history({
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'group': mailing_name,
            'text': message_text,
            'total': len(subscribers),
            'sent': sent,
            'failed': failed
        })

        self.bot.user_sessions.pop(user_id, None)

        return {
            'text': f"✅ *Рассылка завершена!*\n\n"
                    f"📌 Рассылка: *{mailing_name}*\n"
                    f"📨 Отправлено: {sent}\n"
                    f"❌ Ошибок: {failed}",
            'keyboard': self.bot.create_reply_keyboard([
                ["📊 Статистика", "📝 Управление рассылками"],
                ["✉️ Отправить сообщение"]
            ])
        }

    async def _init_mailings(self):
        existing = self.db.get_mailings()

        if existing:
            return

        groups = self.config.get('groups', [])
        if not groups:
            self.db.add_mailing("Все подписчики", "Основная рассылка для всех подписчиков")
            return

        created = 0
        for group in groups:
            name = group.get('name', 'Без названия')
            desc = group.get('desc', '')
            mailing_id = self.db.add_mailing(name, desc)
            if mailing_id:
                created += 1

    async def _get_user_link(self, user_id: int) -> str:
        platform = self.config.get('platform', '')

        if platform == 'tg':
            username = self.config.get(f'username_{user_id}', '')
            if username:
                return f"https://t.me/{username}"
            return f"tg://user?id={user_id}"

        elif platform == 'vk':
            return f"https://vk.com/id{user_id}"

        elif platform == 'max':
            return f"https://max.com/user/{user_id}"

        return f"user_{user_id}"

    def _extract_user_id_from_link(self, user_link: str) -> int:
        try:
            if 'vk.com/id' in user_link:
                user_id_str = user_link.split('/id')[-1]
                return int(user_id_str)
            elif 't.me/' in user_link:
                return 0
            elif 'tg://user?id=' in user_link:
                user_id_str = user_link.split('=')[-1]
                return int(user_id_str)
            else:
                return int(user_link)
        except (ValueError, IndexError, AttributeError) as e:
            self.logger.error(f"Ошибка при извлечении user_id из ссылки: {user_link}: {e}")
            return 0