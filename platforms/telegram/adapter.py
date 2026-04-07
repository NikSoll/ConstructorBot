import asyncio
import logging
from typing import Dict, Any, Optional, List, Union

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import redis

from core.base_bot import BaseBot


class TelegramBot(BaseBot):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.token = config.get('token')
        self.bot = Bot(token=self.token)
        redis_client = redis.from_url(config.get('redis_url', 'redis://localhost:6379/0'))
        self.storage = MemoryStorage()
        self.dp = Dispatcher(storage=self.storage)
        self._register_handlers()

    def _register_handlers(self):
        @self.dp.message(lambda msg: msg.text == "/start")
        async def start_handler(message: types.Message):
            result = await self.handle_start(user_id=message.from_user.id,username=message.from_user.username or "",full_name=message.from_user.full_name,args=message.text.split()[1:] if len(message.text.split()) > 1 else [])
            if result:
                await self.send_message(message.from_user.id,result['text'],keyboard=result.get('keyboard'),edit=False)

        @self.dp.message()
        async def message_handler(message: types.Message):
            result = await self.handle_message( user_id=message.from_user.id, text=message.text)

            if result:
                await self.send_message( message.from_user.id, result['text'], keyboard=result.get('keyboard'), edit=False)

        @self.dp.callback_query()
        async def callback_handler(callback: types.CallbackQuery):
            result = await self.handle_callback( user_id=callback.from_user.id, callback_data=callback.data)
            if result:
                if result.get('edit'):
                    await callback.message.edit_text( result['text'], reply_markup=result.get('keyboard'), parse_mode="Markdown")
                else:
                    await callback.message.answer( result['text'], reply_markup=result.get('keyboard'), parse_mode="Markdown")
            await callback.answer()

    async def notify_admin(self, text: str):
        admin_id = self.config.get('admin_id')
        if admin_id:
            await self.send_message(int(admin_id), text)

    async def send_message(self, user_id: int, text: str, keyboard=None, parse_mode="Markdown", edit: bool = False) -> bool:
        try:
            if edit:
                #не получится - так пишут
                pass
            else:
                await self.bot.send_message( user_id, text, reply_markup=keyboard, parse_mode=parse_mode)
            return True
        except Exception as e:
            self.logger.error(f"Send error: {e}")
            return False

    async def send_photo(self, user_id: int, photo: str, caption: Optional[str] = None, keyboard=None) -> bool:
        try:
            await self.bot.send_photo( user_id, photo, caption=caption, reply_markup=keyboard, parse_mode="Markdown" )
            return True
        except Exception as e:
            self.logger.error(f"Send photo error: {e}")
            return False

    def create_inline_keyboard(self, buttons: List[List[Dict]]) -> InlineKeyboardMarkup:
        keyboard = []
        for row in buttons:
            keyboard_row = []
            for btn in row:
                if 'url' in btn:
                    keyboard_row.append(InlineKeyboardButton(text=btn['text'], url=btn['url']))
                else:
                    keyboard_row.append(InlineKeyboardButton( text=btn['text'], callback_data=btn.get('data', btn.get('callback_data', ''))))
            keyboard.append(keyboard_row)
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    def create_reply_keyboard(self, buttons: List[List[str]], resize: bool = True, one_time: bool = False) -> ReplyKeyboardMarkup:
        keyboard = []
        for row in buttons:
            keyboard_row = [KeyboardButton(text=btn) for btn in row]
            keyboard.append(keyboard_row)
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=resize, one_time_keyboard=one_time)

    async def run(self):
        self.logger.info(f"Starting Telegram bot: {self.config.get('name', 'Unknown')}")
        await self.dp.start_polling(self.bot)