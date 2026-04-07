from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
import logging
import json


class BaseBot(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        self.user_sessions = {}

        self.bot_type = config.get('bot_type')
        self._init_handlers()

    def _init_handlers(self):
        if self.bot_type == 'make':
            from core.handlers.make import MakeHandlers
            self.handlers = MakeHandlers(self)
        elif self.bot_type == 'shop':
            from core.handlers.shop import ShopHandlers
            self.handlers = ShopHandlers(self)
        elif self.bot_type == 'quiz':
            from core.handlers.quiz import QuizHandlers
            self.handlers = QuizHandlers(self)
        elif self.bot_type == 'survey':
            from core.handlers.survey import SurveyHandlers
            self.handlers = SurveyHandlers(self)
        elif self.bot_type == 'mailer':
            from core.handlers.mailer import MailerHandlers
            self.handlers = MailerHandlers(self)
        else:
            raise ValueError(f"Unknown bot type: {self.bot_type}")


    @abstractmethod
    async def send_message(self, user_id: int, text: str, keyboard: Optional[Any] = None, parse_mode: Optional[str] = None, edit: bool = False) -> bool:
        pass

    @abstractmethod
    async def send_photo(self, user_id: int, photo: str, caption: Optional[str] = None, keyboard: Optional[Any] = None) -> bool:
        pass

    @abstractmethod
    def create_inline_keyboard(self, buttons: List[List[Dict]]) -> Any:
        pass

    @abstractmethod
    def create_reply_keyboard(self, buttons: List[List[str]], resize: bool = True, one_time: bool = False) -> Any:
        pass

    async def handle_start(self, user_id: int, username: str = "", full_name: str = "", args: list = None) -> Optional[Dict]:
        if hasattr(self.handlers, 'handle_start'):
            return await self.handlers.handle_start(user_id, username, full_name, args)
        return None

    async def handle_message(self, user_id: int, text: str) -> Optional[Dict]:
        if hasattr(self.handlers, 'handle_message'):
            return await self.handlers.handle_message(user_id, text)
        return None

    async def handle_callback(self, user_id: int, callback_data: str) -> Optional[Dict]:
        if hasattr(self.handlers, 'handle_callback'):
            return await self.handlers.handle_callback(user_id, callback_data)
        return None

    async def notify_admin(self, text: str):
        admin_id = self.config.get('admin_id')
        if admin_id:
            await self.send_message(admin_id, text)

    def get_session(self, user_id: int) -> Dict:
        return self.user_sessions.get(user_id, {})

    def set_session(self, user_id: int, data: Dict):
        self.user_sessions[user_id] = data

    def clear_session(self, user_id: int):
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]