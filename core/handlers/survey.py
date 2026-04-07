from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import json

from ..utils.helpers import get_survey_by_id
from ..database.survey_db import SurveyDatabase


class SurveyHandlers:
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.db = SurveyDatabase(self.config)
        self.logger = logging.getLogger(__name__)

    async def handle_start(self, user_id: int, username: str = "", full_name: str = "", args: list = None) -> Optional[Dict]:
        if user_id in self.bot.user_sessions:
            del self.bot.user_sessions[user_id]

        return {
            'text': self.config['messages']['welcome'],
            'keyboard': self.bot.create_reply_keyboard([
                ["📋 Пройти опрос"],
                ["🏠 Главное меню"]
            ])
        }

    async def handle_message(self, user_id: int, text: str) -> Optional[Dict]:
        session = self.bot.user_sessions.get(user_id, {})
        state = session.get('state')

        if text == "📋 Пройти опрос":
            return await self._show_surveys(user_id)
        elif text == "🏠 Главное меню":
            return await self.handle_start(user_id)

        if state == 'answering':
            return await self._process_text_answer(user_id, text)

        return None

    async def handle_callback(self, user_id: int, callback_data: str) -> Optional[Dict]:
        if user_id not in self.bot.user_sessions:
            self.bot.user_sessions[user_id] = {}

        if callback_data.startswith('survey_'):
            return await self._select_survey(user_id, callback_data)
        elif callback_data.startswith('start_survey_'):
            return await self._start_survey(user_id, callback_data)
        elif callback_data.startswith('single_'):
            return await self._process_single_answer(user_id, callback_data)
        elif callback_data.startswith('multiple_'):
            return await self._process_multiple_answer(user_id, callback_data)
        elif callback_data.startswith('scale_'):
            return await self._process_scale_answer(user_id, callback_data)
        elif callback_data == 'back_to_surveys':
            return await self._show_surveys(user_id, callback=True)

        return None

    async def _show_surveys(self, user_id: int, callback: bool = False) -> Dict:
        if not self.config['surveys']:
            return {
                'text': self.config['messages']['no_surveys'],
                'edit': callback
            }

        buttons = []
        row = []
        for survey in self.config['surveys']:
            row.append({
                'text': survey['name'],
                'data': f"survey_{survey['id']}"
            })
            if len(row) == 2:
                buttons.append(row)
                row = []

        if row:
            buttons.append(row)

        return {
            'text': self.config['messages']['surveys_list'],
            'keyboard': self.bot.create_inline_keyboard(buttons),
            'edit': callback
        }

    async def _select_survey(self, user_id: int, callback_data: str) -> Optional[Dict]:
        survey_id = int(callback_data.split('_')[1])
        survey = get_survey_by_id(survey_id, self.config['surveys'])

        if not survey:
            return None

        self.bot.user_sessions[user_id]['survey_id'] = survey_id
        self.bot.user_sessions[user_id]['state'] = 'survey_start'

        text = self.config['messages']['survey_start'].format(
            name=survey['name'],
            description=survey['description'],
            questions=len(survey['questions'])
        )

        buttons = [[{
            'text': "▶️ Начать опрос",
            'data': f"start_survey_{survey_id}"
        }]]

        return {
            'text': text,
            'keyboard': self.bot.create_inline_keyboard(buttons)
        }

    async def _start_survey(self, user_id: int, callback_data: str) -> Optional[Dict]:
        survey_id = int(callback_data.split('_')[2])
        survey = get_survey_by_id(survey_id, self.config['surveys'])

        if not survey:
            return None

        self.bot.user_sessions[user_id].update({
            'survey_id': survey_id,
            'current_q': 0,
            'answers': [],
            'multiple_answers': [],
            'state': 'answering'
        })

        return await self._show_question(user_id, survey_id, 0)

    async def _show_question(self, user_id: int, survey_id: int, q_index: int) -> Optional[Dict]:
        survey = get_survey_by_id(survey_id, self.config['surveys'])
        if not survey or q_index >= len(survey['questions']):
            return None

        question = survey['questions'][q_index]
        session = self.bot.user_sessions.get(user_id, {})

        if question['type'] == 'text':
            text = self.config['messages']['question_text'].format(
                current=q_index + 1,
                total=len(survey['questions']),
                text=question['text']
            )
            reply_markup = None


        elif question['type'] == 'single':
            text = self.config['messages']['question_single'].format(
                current=q_index + 1,
                total=len(survey['questions']),
                text=question['text']
            )

            buttons = []
            row = []
            for i, option in enumerate(question['options']):
                row.append({
                    'text': option,
                    'data': f"single_{survey_id}_{q_index}_{i}"
                })
                if len(row) == 2:
                    buttons.append(row)
                    row = []
            if row:
                buttons.append(row)
            reply_markup = self.bot.create_inline_keyboard(buttons)

        elif question['type'] == 'multiple':
            text = self.config['messages']['question_multiple'].format(
                current=q_index + 1,
                total=len(survey['questions']),
                text=question['text']
            )

            buttons = []
            multiple_answers = session.get('multiple_answers', [])

            for i, option in enumerate(question['options']):
                check = "✅ " if i in multiple_answers else ""
                buttons.append([{
                    'text': f"{check}{option}",
                    'data': f"multiple_{survey_id}_{q_index}_select_{i}"
                }])
            buttons.append([{
                'text': "✅ Готово",
                'data': f"multiple_{survey_id}_{q_index}_done"
            }])
            reply_markup = self.bot.create_inline_keyboard(buttons)


        elif question['type'] == 'scale':
            min_val = question.get('min', 1)
            max_val = question.get('max', 5)
            text = self.config['messages']['question_scale'].format(
                current=q_index + 1,
                total=len(survey['questions']),
                text=question['text'],
                min=min_val,
                max=max_val
            )
            buttons = []
            row = []
            for i in range(min_val, max_val + 1):
                row.append({
                    'text': str(i),
                    'data': f"scale_{survey_id}_{q_index}_{i}"
                })
                if len(row) == 5:
                    buttons.append(row)
                    row = []
            if row:
                buttons.append(row)
            reply_markup = self.bot.create_inline_keyboard(buttons)
        else:
            return None

        return {
            'text': text,
            'keyboard': reply_markup
        }

    async def _process_single_answer(self, user_id: int, callback_data: str) -> Optional[Dict]:
        parts = callback_data.split('_')
        survey_id = int(parts[1])
        q_index = int(parts[2])
        answer_index = int(parts[3])

        survey = get_survey_by_id(survey_id, self.config['surveys'])
        if not survey or q_index >= len(survey['questions']):
            return None

        question = survey['questions'][q_index]
        answer_text = question['options'][answer_index]

        session = self.bot.user_sessions.get(user_id, {})
        answers = session.get('answers', [])
        answers.append({
            'question': question['text'],
            'answer': answer_text,
            'type': 'single'
        })
        session['answers'] = answers
        self.bot.user_sessions[user_id] = session

        return await self._next_question(user_id, survey_id, q_index)

    async def _process_multiple_answer(self, user_id: int, callback_data: str) -> Optional[Dict]:
        parts = callback_data.split('_')
        survey_id = int(parts[1])
        q_index = int(parts[2])
        action = parts[3]

        survey = get_survey_by_id(survey_id, self.config['surveys'])
        if not survey or q_index >= len(survey['questions']):
            return None

        question = survey['questions'][q_index]
        session = self.bot.user_sessions.get(user_id, {})
        multiple_answers = session.get('multiple_answers', [])

        if action == "select":
            option_index = int(parts[4])

            if option_index in multiple_answers:
                multiple_answers.remove(option_index)
            else:
                multiple_answers.append(option_index)

            session['multiple_answers'] = multiple_answers
            self.bot.user_sessions[user_id] = session

            return await self._show_question(user_id, survey_id, q_index)

        elif action == "done":
            if multiple_answers:
                selected_options = [question['options'][i] for i in multiple_answers]
                answers = session.get('answers', [])
                answers.append({
                    'question': question['text'],
                    'answer': ", ".join(selected_options),
                    'type': 'multiple',
                    'selected': selected_options
                })
                session['answers'] = answers
                session['multiple_answers'] = []
                self.bot.user_sessions[user_id] = session

                return await self._next_question(user_id, survey_id, q_index)

        return None

    async def _process_scale_answer(self, user_id: int, callback_data: str) -> Optional[Dict]:
        parts = callback_data.split('_')
        survey_id = int(parts[1])
        q_index = int(parts[2])
        value = int(parts[3])

        survey = get_survey_by_id(survey_id, self.config['surveys'])
        if not survey or q_index >= len(survey['questions']):
            return None

        question = survey['questions'][q_index]

        session = self.bot.user_sessions.get(user_id, {})
        answers = session.get('answers', [])
        answers.append({
            'question': question['text'],
            'answer': value,
            'type': 'scale'
        })
        session['answers'] = answers
        self.bot.user_sessions[user_id] = session

        return await self._next_question(user_id, survey_id, q_index)

    async def _process_text_answer(self, user_id: int, text: str) -> Optional[Dict]:
        session = self.bot.user_sessions.get(user_id, {})
        survey_id = session.get('survey_id')
        q_index = session.get('current_q', 0)

        survey = get_survey_by_id(survey_id, self.config['surveys'])
        if not survey or q_index >= len(survey['questions']):
            return None

        question = survey['questions'][q_index]

        answers = session.get('answers', [])
        answers.append({
            'question': question['text'],
            'answer': text,
            'type': 'text'
        })
        session['answers'] = answers
        self.bot.user_sessions[user_id] = session

        return await self._next_question(user_id, survey_id, q_index)

    async def _next_question(self, user_id: int, survey_id: int, q_index: int) -> Optional[Dict]:
        survey = get_survey_by_id(survey_id, self.config['surveys'])
        next_q = q_index + 1

        if next_q < len(survey['questions']):
            session = self.bot.user_sessions.get(user_id, {})
            session['current_q'] = next_q
            self.bot.user_sessions[user_id] = session
            return await self._show_question(user_id, survey_id, next_q)
        else:
            return await self._finish_survey(user_id, survey_id)

    async def _finish_survey(self, user_id: int, survey_id: int) -> Dict:
        session = self.bot.user_sessions.get(user_id, {})
        survey = get_survey_by_id(survey_id, self.config['surveys'])

        survey_result = {
            'user_id': user_id,
            'username': session.get('username', ''),
            'survey_id': survey_id,
            'survey_name': survey['name'],
            'answers': session.get('answers', []),
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        self.db.save_survey_result(survey_result)

        if user_id in self.bot.user_sessions:
            del self.bot.user_sessions[user_id]

        buttons = [[{
            'text': "📋 Другие опросы",
            'data': "back_to_surveys"
        }]]

        return {
            'text': self.config['messages']['thanks'],
            'keyboard': self.bot.create_inline_keyboard(buttons)
        }