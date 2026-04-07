from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from ..utils.helpers import format_date, get_master_by_id
from ..database.make_db import MakeDatabase


class MakeHandlers:
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.db = MakeDatabase(self.config)
        self.logger = logging.getLogger(__name__)

#приветствие и главное меню
    async def handle_start(self, user_id: int, username: str = "", full_name: str = "", args: list = None) -> Optional[Dict]:
        if user_id in self.bot.user_sessions:
            del self.bot.user_sessions[user_id]

        return {
            'text': self.config['messages']['welcome'].format(
                name=self.config['salon_settings']['name']
            ),
            'keyboard': self.bot.create_reply_keyboard([
                ["📝 Записаться", "🎨 Примеры работ"],
                ["📞 Контакты"]
            ])
        }
#обрабатывает текст. сообщ
    async def handle_message(self, user_id: int, text: str) -> Optional[Dict]:
        session = self.bot.user_sessions.get(user_id, {})
        state = session.get('state')

        if text == "📝 Записаться":
            return await self._start_booking(user_id)

        elif text == "🎨 Примеры работ":
            return await self._show_works(user_id)

        elif text == "📞 Контакты":
            return {
                'text': self.config['messages']['contacts'].format(
                    address=self.config['salon_settings']['address'],
                    hours=self.config['salon_settings']['working_hours'],
                    phone=self.config['salon_settings']['phone']
                )
            }

        elif text == "❌ Отменить запись":
            if user_id in self.bot.user_sessions:
                del self.bot.user_sessions[user_id]
            return {
                'text': "❌ Оформление записи отменено",
                'keyboard': self.bot.create_reply_keyboard([
                    ["📝 Записаться", "🎨 Примеры работ"],
                    ["📞 Контакты"]
                ])
            }

        if state == 'entering_name':
            return await self._process_name(user_id, text)

        elif state == 'entering_phone':
            return await self._process_phone(user_id, text)

        elif state == 'entering_comment':
            return await self._process_comment(user_id, text)

        elif state == 'entering_date':
            return await self._process_date(user_id, text)

        elif state == 'entering_time':
            return await self._process_time(user_id, text)

        return None
#нажатие на инлайн кнопки
    async def handle_callback(self, user_id: int, callback_data: str) -> Optional[Dict]:
        self.logger.info(f"Callback от {user_id}: {callback_data}")

        if user_id not in self.bot.user_sessions:
            self.bot.user_sessions[user_id] = {}


        if callback_data.startswith('master_'):
            return await self._choose_master(user_id, callback_data)

        elif callback_data.startswith('service_'):
            return await self._choose_service(user_id, callback_data)

        elif callback_data == 'back_to_masters':
            return await self._back_to_masters(user_id)

        elif callback_data == 'time_next_page':
            self.bot.user_sessions[user_id]['time_page'] = self.bot.user_sessions[user_id].get('time_page', 0) + 1
            return await self._show_time_page(user_id)
        elif callback_data == 'time_prev_page':
            self.bot.user_sessions[user_id]['time_page'] = max(0, self.bot.user_sessions[user_id].get('time_page', 0) - 1)
            return await self._show_time_page(user_id)

        elif callback_data == 'cancel':
            if user_id in self.bot.user_sessions:
                del self.bot.user_sessions[user_id]
            return {
                'text': "❌ Действие отменено",
                'keyboard': self.bot.create_reply_keyboard([
                    ["📝 Записаться", "🎨 Примеры работ"],
                    ["📞 Контакты"]
                ])
            }

        return None

    async def _start_booking(self, user_id: int) -> Dict:
        self.bot.user_sessions[user_id] = {'state': 'choosing_master'}

        #текст с описанием мастеров
        masters_text = "👩‍🎨 *Выберите мастера:*\n\n"
        for master in self.config['masters']:
            masters_text += f"{master['emoji']} *{master['name']}*\n"
            masters_text += f"   📌 Специализация: {master.get('specialty', 'не указана')}\n"
            masters_text += f"   📝 {master.get('desc', 'нет описания')}\n\n"

        #кнопки с именами
        buttons = []
        for master in self.config['masters']:
            buttons.append([{
                'text': f"{master['emoji']} {master['name']}",
                'data': f"master_{master['id']}"
            }])
        buttons.append([{'text': "❌ Отмена", 'data': "cancel"}])

        return {
            'text': masters_text,
            'keyboard': self.bot.create_inline_keyboard(buttons)
        }

#ывыбор мастера
    async def _choose_master(self, user_id: int, callback_data: str) -> Optional[Dict]:
        master_id = int(callback_data.split('_')[1])
        master = get_master_by_id(master_id, self.config['masters'])

        if not master:
            return None

        self.bot.user_sessions[user_id]['master'] = master['name']
        self.bot.user_sessions[user_id]['master_id'] = master_id
        self.bot.user_sessions[user_id]['state'] = 'entering_date'  #новое состояние

        services_text = "💇 *Выберите услугу:*\n\n"
        for service in self.config['services']:
            price = service.get('price', 'не указана')
            duration = service.get('duration', 'не указана')
            desc = service.get('desc', '')
            services_text += f"💎 *{service['name']}*\n"
            services_text += f"   💰 Цена: {price}₽\n"
            services_text += f"   ⏱️ Длительность: {duration} мин\n"
            if desc:
                services_text += f"   📝 {desc}\n"
            services_text += "\n"

        #кнопки с услугами
        buttons = []
        for service in self.config['services']:
            buttons.append([{
                'text': service['name'],
                'data': f"service_{service['id']}"
            }])
        buttons.append([{'text': "❌ Отмена", 'data': "cancel"}])

        return {
            'text': f"👩‍🎨 Выбран мастер: *{master['emoji']} {master['name']}*\n\n{services_text}",
            'keyboard': self.bot.create_inline_keyboard(buttons)
        }

    async def _process_name(self, user_id: int, text: str) -> Dict:
        self.bot.user_sessions[user_id]['name'] = text
        self.bot.user_sessions[user_id]['state'] = 'entering_phone'

        return {
            'text': self.config['messages']['enter_phone'],
            'keyboard': self.bot.create_reply_keyboard([["❌ Отменить запись"]])
        }

    async def _process_phone(self, user_id: int, text: str) -> Dict:
        self.bot.user_sessions[user_id]['phone'] = text
        self.bot.user_sessions[user_id]['state'] = 'entering_comment'

        return {
            'text': self.config['messages']['enter_comment']
        }

    async def _process_comment(self, user_id: int, text: str) -> Dict:
        comment = text if text != "-" else ""

        #все дан
        data = self.bot.user_sessions.get(user_id, {})
        booking_data = {
            'user_id': user_id,
            'username': data.get('username', ''),
            'name': data.get('name'),
            'phone': data.get('phone'),
            'service': data.get('service'),
            'master': data.get('master'),
            'date': data.get('date'),
            'time': data.get('time'),
            'comment': comment,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        #сейв гугл щитс
        success = self.db.add_booking(booking_data)

        #чист сессия
        if user_id in self.bot.user_sessions:
            del self.bot.user_sessions[user_id]

        if success:
            #уведом админу
            if self.config['salon_settings'].get('admin_chat_id'):
                admin_text = (f"📥 *Новая запись!*\n\n"
                              f"• Услуга: {data.get('service')}\n"
                              f"• Клиент: {booking_data['name']}\n"
                              f"• Телефон: {booking_data['phone']}\n"
                              f"• Мастер: {booking_data['master']}\n"
                              f"• Дата: {format_date(booking_data['date'])} {booking_data['time']}\n"
                              f"• Комментарий: {booking_data['comment'] or 'нет'}")
                await self.bot.notify_admin(admin_text)

            return {
                'text': self.config['messages']['booking_success'].format(
                    master=booking_data['master'],
                    date=format_date(booking_data['date']),
                    time=booking_data['time'],
                    phone=booking_data['phone']
                ),
                'keyboard': self.bot.create_reply_keyboard([
                    ["📝 Записаться", "🎨 Примеры работ"],
                    ["📞 Контакты"]
                ])
            }
        else:
            return {
                'text': self.config['messages']['booking_error'].format(
                    phone=self.config['salon_settings']['phone']
                ),
                'keyboard': self.bot.create_reply_keyboard([
                    ["📝 Записаться", "🎨 Примеры работ"],
                    ["📞 Контакты"]
                ])
            }

    async def _back_to_masters(self, user_id: int) -> Dict:
        self.bot.user_sessions[user_id]['state'] = 'choosing_master'

        buttons = []
        row = []
        for master in self.config['masters']:
            row.append({
                'text': f"{master['emoji']} {master['name']}",
                'data': f"master_{master['id']}"
            })
            if len(row) == 3:
                buttons.append(row)
                row = []

        if row:
            buttons.append(row)

        buttons.append([{'text': "❌ Отмена", 'data': "cancel"}])

        return {
            'text': self.config['messages']['choose_master'],
            'keyboard': self.bot.create_inline_keyboard(buttons)
        }

    async def _process_date(self, user_id: int, text: str) -> Dict:
        import re
        if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', text):
            return {
                'text': "❌ *Неверный формат!*\n\n"
                        f"Введите дату в формате: *ДД.ММ.ГГГГ*\n"
                        f"Например: 25.03.2025",
                'keyboard': self.bot.create_reply_keyboard([["❌ Отменить запись"]])
            }

        self.bot.user_sessions[user_id]['date'] = text
        self.bot.user_sessions[user_id]['state'] = 'entering_time'  # новое состояние

        return {
            'text': f"📅 Выбрана дата: *{text}*\n\n"
                    f"🕐 *Введите время в формате ЧЧ:ММ*\n"
                    f"Например: 14:30",
            'keyboard': self.bot.create_reply_keyboard([["❌ Отменить запись"]])
        }

    async def _process_time(self, user_id: int, text: str) -> Dict:
        import re
        if not re.match(r'^\d{2}:\d{2}$', text):
            return {
                'text': "❌ *Неверный формат!*\n\n"
                        f"Введите время в формате: *ЧЧ:ММ*\n"
                        f"Например: 14:30",
                'keyboard': self.bot.create_reply_keyboard([["❌ Отменить запись"]])
            }

        times = self.config.get('available_times', [])
        if text not in times:
            return {
                'text': f"❌ *Время {text} недоступно!*\n\n"
                        f"Доступное время: {', '.join(times)}",
                'keyboard': self.bot.create_reply_keyboard([["❌ Отменить запись"]])
            }

        self.bot.user_sessions[user_id]['time'] = text
        self.bot.user_sessions[user_id]['state'] = 'entering_name'

        data = self.bot.user_sessions[user_id]

        return {
            'text': f"✅ *Предварительные данные:*\n"
                    f"• Мастер: {data.get('master')}\n"
                    f"• Дата: {data.get('date')}\n"
                    f"• Время: {text}\n\n"
                    f"{self.config['messages']['enter_name']}",
            'keyboard': self.bot.create_reply_keyboard([["❌ Отменить запись"]])
        }
#выбор услуги
    async def _choose_service(self, user_id: int, callback_data: str) -> Optional[Dict]:
        service_id = int(callback_data.split('_')[1])
        service = next((s for s in self.config['services'] if s['id'] == service_id), None)

        if not service:
            return None

        self.bot.user_sessions[user_id]['service'] = service['name']
        self.bot.user_sessions[user_id]['service_id'] = service_id
        self.bot.user_sessions[user_id]['state'] = 'entering_date'

        return {
            'text': f"✅ Выбрана услуга: *{service['name']}*\n\n"
                    f"📅 *Введите дату в формате ДД.ММ.ГГГГ*\n"
                    f"Например: 25.03.2025",
            'keyboard': self.bot.create_reply_keyboard([["❌ Отменить запись"]])
        }

    async def _show_time_page(self, user_id: int) -> Dict:
        page = self.bot.user_sessions[user_id].get('time_page', 0)
        times = self.config.get('available_times',
                                ["10:00", "11:00", "12:00", "13:00", "14:00",
                                 "15:00", "16:00", "17:00", "18:00", "19:00"])

        per_page = 5
        start = page * per_page
        end = start + per_page
        page_times = times[start:end]

        buttons = []
        for time in page_times:
            buttons.append([{
                'text': time,
                'data': f"time_{time}"
            }])

        nav_row = []
        if page > 0:
            nav_row.append({'text': "⬅️ Назад", 'data': "time_prev_page"})
        if end < len(times):
            nav_row.append({'text': "➡️ Далее", 'data': "time_next_page"})

        if nav_row:
            buttons.append(nav_row)

        buttons.append([{'text': "❌ Отмена", 'data': "cancel"}])

        return {
            'text': f"📅 Выбрана дата: *{self.bot.user_sessions[user_id]['date']}*\n\n"
                    f"Выберите время (страница {page + 1} из {(len(times) - 1) // per_page + 1}):",
            'keyboard': self.bot.create_inline_keyboard(buttons)
        }

    async def _show_works(self, user_id: int) -> Dict:
        masters = self.config.get('masters', [])
        has_photos = any(m.get('photo') for m in masters)

        if not has_photos:
            return {
                'text': "🎨 Мы пока не успели добавить фото работ.\n\nЗагляните позже!"
            }

        for master in masters:
            if master.get('photo'):
                await self.bot.send_photo(
                    user_id,
                    master['photo'],
                    caption=f"👩‍🎨 {master['emoji']} {master['name']}\n📌 {master.get('specialty', '')}"
                )

        return {
            'text': "✨ Вот примеры работ наших мастеров:",
            'keyboard': self.bot.create_reply_keyboard([
                ["📝 Записаться", "🎨 Примеры работ"],
                ["📞 Контакты"]
            ])
        }