import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import json
import logging
import asyncio
import time
from typing import Dict, Any, Optional, List
from threading import Thread
from core.base_bot import BaseBot

#дочерний класс для core/base_bot
class VKBot(BaseBot):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.token = config.get('token')
        self.group_id = config.get('group_id')
        self.vk_session = vk_api.VkApi(token=self.token)
        self.vk = self.vk_session.get_api()
        self.longpoll = VkBotLongPoll(self.vk_session, self.group_id)
        self.loop = None
        self._last_message_time = {}
        self.logger.info(f"VK бот инициализирован для группы {self.group_id}")

#тправка сообщений(синхронный)
    def send_message_sync(self, user_id, text, keyboard=None):
        try:
            clean_text = text.replace('*', '').replace('_', '').replace('`', '')
            params = {
                'user_id': int(user_id),
                'message': clean_text,
                'random_id': 0
            }
            if keyboard:
                if hasattr(keyboard, 'get_keyboard'):
                    params['keyboard'] = keyboard.get_keyboard()
                else:
                    params['keyboard'] = keyboard
            self.vk.messages.send(**params)
            return True
        except Exception as e:
            self.logger.error(f"Ошибка отправки: {e}")
            return False

#отправка сообщений(асинхронный)
    async def send_message(self, user_id: int, text: str, keyboard=None, parse_mode=None, edit: bool = False) -> bool:
        try:
            clean_text = text.replace('*', '').replace('_', '').replace('`', '')
            params = {
                'user_id': int(user_id),
                'message': clean_text,
                'random_id': 0
            }
            if keyboard:
                if hasattr(keyboard, 'get_keyboard'):
                    params['keyboard'] = keyboard.get_keyboard()
                else:
                    params['keyboard'] = keyboard

            self.vk.messages.send(**params)
            return True
        except Exception as e:
            self.logger.error(f"Ошибка отправки VK: {e}", exc_info=True)
            return False

    async def send_photo(self, user_id: int, photo: str, caption: Optional[str] = None, keyboard=None) -> bool:
        try:
            upload_url = self.vk.photos.getMessagesUploadServer()

            import requests
            img_data = requests.get(photo).content
            with open('temp.jpg', 'wb') as f:
                f.write(img_data)

            upload = requests.post(upload_url['upload_url'], files={'photo': open('temp.jpg', 'rb')}).json()

            photo_obj = self.vk.photos.saveMessagesPhoto(
                photo=upload['photo'],
                server=upload['server'],
                hash=upload['hash']
            )[0]

            params = {
                'user_id': user_id,
                'attachment': f"photo{photo_obj['owner_id']}_{photo_obj['id']}",
                'random_id': 0
            }
            if caption:
                params['message'] = caption
            if keyboard:
                if hasattr(keyboard, 'get_keyboard'):
                    params['keyboard'] = keyboard.get_keyboard()
                else:
                    params['keyboard'] = keyboard

            self.vk.messages.send(**params)
            return True
        except Exception as e:
            self.logger.error(f"Ошибка отправки фото VK: {e}")
            return False

#создание инлайн клавиатуры
    def create_inline_keyboard(self, buttons: List[List[Dict]]) -> VkKeyboard:
        keyboard = VkKeyboard(inline=True)

        for i, row in enumerate(buttons):
            if not row:
                continue
            for btn in row:
                color = VkKeyboardColor.PRIMARY
                if btn.get('color') == 'green':
                    color = VkKeyboardColor.POSITIVE
                elif btn.get('color') == 'red':
                    color = VkKeyboardColor.NEGATIVE

                payload = {'command': btn.get('data', btn.get('callback_data', ''))}
                keyboard.add_button(
                    label=btn['text'],
                    color=color,
                    payload=json.dumps(payload)
                )
            if i < len(buttons) - 1:
                keyboard.add_line()

        return keyboard

#ссоздание обчной клавиатуры
    def create_reply_keyboard(self, buttons: List[List[str]], resize: bool = True,
                              one_time: bool = False) -> VkKeyboard:
        keyboard = VkKeyboard(one_time=one_time)
        for i, row in enumerate(buttons):
            for j, btn in enumerate(row):
                keyboard.add_button(btn, color=VkKeyboardColor.PRIMARY)
                if j < len(row) - 1:
                    keyboard.add_line()
            if i < len(buttons) - 1:
                keyboard.add_line()
        return keyboard

#бработка сообщения
    def _handle_event(self, event):
        if event.type == VkBotEventType.MESSAGE_NEW:
            msg = event.obj.message
            user_id = int(msg['from_id'])
            text = msg.get('text', '')

            current_time = time.time()
            if current_time - self._last_message_time.get(user_id, 0) < 1.0:
                return
            self._last_message_time[user_id] = current_time

            callback_data = None
            if 'payload' in msg:
                try:
                    payload_data = json.loads(msg['payload'])
                    callback_data = payload_data.get('command', '')
                except Exception as e:
                    self.logger.error(f"Ошибка парсинга payload: {e}")

            try:
                user_info = self.vk.users.get(user_ids=user_id)[0]
                username = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
                full_name = username
            except Exception:
                username = f"user_{user_id}"
                full_name = username

            if callback_data:
                coro = self.handle_callback(user_id, callback_data)
            else:
                if text == "/start" or text == "Начать":
                    coro = self.handle_start(user_id, username, full_name)
                else:
                    coro = self.handle_message(user_id, text)

            try:
                future = asyncio.run_coroutine_threadsafe(coro, self.loop)
                result = future.result(timeout=15)
                self.logger.info(f"Результат выполнения: {result}")

                if result and isinstance(result, dict) and result.get('text'):
                    self.send_message_sync(user_id, result['text'], result.get('keyboard'))
            except TimeoutError:
                self.logger.error(f"Таймаут обработки запроса для пользователя {user_id}")
            except Exception as e:
                self.logger.error(f"Ошибка обработки результата для пользователя {user_id}: {e}", exc_info=True)

#запуск
    def run(self):
        self.logger.info(f"Запуск VK бота для группы {self.group_id}")

        def start_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            if hasattr(self.handlers, '_init_mailings'):
                try:
                    self.loop.run_until_complete(self.handlers._init_mailings())
                except Exception as e:
                    self.logger.error(f"Ошибка инициализации рассылок: {e}")

            self.loop.run_forever()

        thread = Thread(target=start_loop, daemon=True)
        thread.start()

        import time
        time.sleep(0.5)

        for event in self.longpoll.listen():
            try:
                self._handle_event(event)
            except Exception as e:
                self.logger.error(f"Ошибка обработки события: {e}")

    def stop(self):
        self.logger.info("Остановка бота...")
        self.is_running = False