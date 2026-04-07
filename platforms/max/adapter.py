import asyncio
import logging
from typing import Dict, Any, Optional, List, Union

try:
    from max_sdk import MaxBot as MaxSDKBot
    from max_sdk.types import Message, CallbackQuery
except ImportError:
    #пока та4к
    logging.warning("max_sdk not installed, using stub")
    MaxSDKBot = object
    Message = object
    CallbackQuery = object
from core.base_bot import BaseBot

class MaxBotAdapter(BaseBot):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.bot_id = config.get('bot_id')
        self.secret_key = config.get('secret_key')
        self.webhook_url = config.get('webhook_url')
        self.bot = MaxSDKBot(api_key=self.api_key, bot_id=self.bot_id,secret_key=self.secret_key)
        self._register_handlers()
        self.logger.info(f"Max Bot initialized for bot {self.bot_id}")

    def _register_handlers(self):
        @self.bot.on_message("text")
        async def message_handler(event):
            user_id = event.user_id
            text = event.text
            if text == "/start":
                result = await self.handle_start(user_id=user_id,username=event.username or "",full_name=event.full_name or "")
            else:
                result = await self.handle_message(user_id, text)

            if result:
                await self.send_message(user_id,result['text'], keyboard=result.get('keyboard'))

        @self.bot.on_callback()
        async def callback_handler(event):
            user_id = event.user_id
            callback_data = event.data
            result = await self.handle_callback(user_id, callback_data)
            if result:
                await self.send_message(user_id,result['text'],keyboard=result.get('keyboard'))

    async def send_message(self, user_id: int, text: str,keyboard=None, parse_mode=None,edit: bool = False) -> bool:
        try:
            if keyboard and hasattr(keyboard, 'to_dict'):
                keyboard_dict = keyboard.to_dict()
            else:
                keyboard_dict = keyboard
            await self.bot.send_message(user_id=user_id, text=text,keyboard=keyboard_dict)
            return True

        except Exception as e:
            self.logger.error(f"Max send error: {e}")
            return False

    async def send_photo(self, user_id: int, photo: str, caption: Optional[str] = None,keyboard=None) -> bool:
        try:
            await self.bot.send_photo(user_id=user_id,photo=photo,caption=caption,keyboard=keyboard)
            return True

        except Exception as e:
            self.logger.error(f"Max send photo error: {e}")
            return False

    def create_inline_keyboard(self, buttons: List[List[Dict]]) -> Any:
        max_buttons = []
        for row in buttons:
            max_row = []
            for btn in row:
                max_row.append({
                    'text': btn['text'],
                    'data': btn.get('data', btn.get('callback_data', '')),
                    'url': btn.get('url')
                })
            max_buttons.append(max_row)
        return {'inline_keyboard': max_buttons}

    def create_reply_keyboard(self, buttons: List[List[str]], resize: bool = True,one_time: bool = False) -> Any:
        return {
            'keyboard': buttons,
            'resize_keyboard': resize,
            'one_time_keyboard': one_time
        }

    async def run(self):
        self.logger.info(f"Starting Max bot {self.bot_id}")
        if self.webhook_url:
            await self.bot.start_webhook(webhook_url=self.webhook_url,port=self.config.get('port', 5000))
        else:
            await self.bot.start_polling()
        await asyncio.Event().wait()