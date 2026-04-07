from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from ..utils.helpers import get_quiz_by_id
from ..database.quiz_db import QuizDatabase


class QuizHandlers:
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.db = QuizDatabase(self.config)
        self.logger = logging.getLogger(__name__)

    async def handle_start(self, user_id: int, username: str = "", full_name: str = "", args: list = None) -> Optional[Dict]:
        if user_id in self.bot.user_sessions:
            del self.bot.user_sessions[user_id]

        return {
            'text': self.config['messages']['welcome'],
            'keyboard': self.bot.create_reply_keyboard([
                ["🎯 Квизы"],
                ["🏠 Главное меню"]
            ])
        }

    async def handle_message(self, user_id: int, text: str) -> Optional[Dict]:
        if text == "🎯 Квизы":
            return await self._show_quizzes(user_id)

        elif text == "🏠 Главное меню":
            return await self.handle_start(user_id)

        return None

    async def handle_callback(self, user_id: int, callback_data: str) -> Optional[Dict]:
        self.logger.info(f"Квиз callback от {user_id}: {callback_data}")

        if user_id not in self.bot.user_sessions:
            self.bot.user_sessions[user_id] = {}


        if callback_data.startswith('quiz_'):
            return await self._select_quiz(user_id, callback_data)

        elif callback_data.startswith('start_quiz_'):
            return await self._start_quiz(user_id, callback_data)

        elif callback_data.startswith('answer_'):
            return await self._process_answer(user_id, callback_data)

        elif callback_data == 'back_to_quizzes':
            return await self._show_quizzes(user_id, callback=True)

        return None

    async def _show_quizzes(self, user_id: int, callback: bool = False) -> Dict:
        quizzes = self.config.get('quizzes', [])
        if not quizzes:
            return {
                'text': self.config['messages']['no_quizzes'],
                'edit': callback
            }

        buttons = []
        row = []
        for quiz in quizzes:
            row.append({
                'text': quiz['name'],
                'data': f"quiz_{quiz['id']}"
            })
            if len(row) == 2:
                buttons.append(row)
                row = []

        if row:
            buttons.append(row)

        return {
            'text': "Выберите квиз:",
            'keyboard': self.bot.create_inline_keyboard(buttons),
            'edit': callback
        }

    async def _select_quiz(self, user_id: int, callback_data: str) -> Optional[Dict]:
        quiz_id = int(callback_data.split('_')[1])
        quiz = get_quiz_by_id(quiz_id, self.config['quizzes'])

        if not quiz:
            return None

        self.bot.user_sessions[user_id]['quiz_id'] = quiz_id
        self.bot.user_sessions[user_id]['state'] = 'quiz_start'

        text = self.config['messages']['quiz_start'].format(
            name=quiz['name'],
            description=quiz['description'],
            questions=len(quiz['questions'])
        )

        buttons = [[{
            'text': "▶️ Начать квиз",
            'data': f"start_quiz_{quiz_id}"
        }]]

        return {
            'text': text,
            'keyboard': self.bot.create_inline_keyboard(buttons)
        }

    async def _start_quiz(self, user_id: int, callback_data: str) -> Optional[Dict]:
        quiz_id = int(callback_data.split('_')[2])
        quiz = get_quiz_by_id(quiz_id, self.config['quizzes'])

        if not quiz:
            return None

        self.bot.user_sessions[user_id].update({
            'quiz_id': quiz_id,
            'current_q': 0,
            'answers': [],
            'points': {}
        })

        return await self._show_question(user_id, quiz_id, 0)

    async def _show_question(self, user_id: int, quiz_id: int, q_index: int) -> Optional[Dict]:
        quiz = get_quiz_by_id(quiz_id, self.config['quizzes'])
        if not quiz or q_index >= len(quiz['questions']):
            return None

        question = quiz['questions'][q_index]

        text = self.config['messages']['question'].format(
            current=q_index + 1,
            total=len(quiz['questions']),
            text=question['text']
        )

        buttons = []
        row = []
        for i, option in enumerate(question['options']):
            row.append({
                'text': option['text'],
                'data': f"answer_{quiz_id}_{q_index}_{i}"
            })
            if len(row) == 2:
                buttons.append(row)
                row = []

        if row:
            buttons.append(row)

        return {
            'text': text,
            'keyboard': self.bot.create_inline_keyboard(buttons)
        }

    async def _process_answer(self, user_id: int, callback_data: str) -> Optional[Dict]:
        parts = callback_data.split('_')
        quiz_id = int(parts[1])
        q_index = int(parts[2])
        answer_index = int(parts[3])

        quiz = get_quiz_by_id(quiz_id, self.config['quizzes'])
        if not quiz or q_index >= len(quiz['questions']):
            return None

        question = quiz['questions'][q_index]
        selected_option = question['options'][answer_index]

        session = self.bot.user_sessions.get(user_id, {})
        answers = session.get('answers', [])
        points = session.get('points', {})

        answers.append({
            'question': question['text'],
            'answer': selected_option['text']
        })

        for category, point_value in selected_option['points'].items():
            points[category] = points.get(category, 0) + point_value

        session['answers'] = answers
        session['points'] = points
        self.bot.user_sessions[user_id] = session

        next_q = q_index + 1
        if next_q < len(quiz['questions']):
            session['current_q'] = next_q
            return await self._show_question(user_id, quiz_id, next_q)
        else:
            return await self._show_result(user_id, quiz_id)

    async def _show_result(self, user_id: int, quiz_id: int) -> Optional[Dict]:
        session = self.bot.user_sessions.get(user_id, {})
        points = session.get('points', {})

        quiz = get_quiz_by_id(quiz_id, self.config['quizzes'])
        if not quiz:
            return None

        total_score = sum(points.values())

        result_text = "Результат не определен"
        for result in quiz['results']:
            if total_score >= result.get('min_score', 0):
                result_text = result['text']
                break

        self.db.save_result({
            'user_id': user_id,
            'username': session.get('username', ''),
            'quiz_id': quiz_id,
            'quiz_name': quiz['name'],
            'result': result_text,
            'points': points,
            'total_score': total_score,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        if user_id in self.bot.user_sessions:
            del self.bot.user_sessions[user_id]

        buttons = [[{
            'text': "🎯 Другие квизы",
            'data': "back_to_quizzes"
        }]]

        return {
            'text': f"🎉 *Ваш результат:*\n\n{result_text}\n\n🏆 Набрано баллов: {total_score}",
            'keyboard': self.bot.create_inline_keyboard(buttons)
        }

