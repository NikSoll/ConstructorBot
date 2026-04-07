import zipfile
import io
import os
import requests
import json

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import current_user, login_required

from app import db
from app.models import User, Bot
from app.bot_generator import BotGenerator


main_bp = Blueprint('main', __name__)
generator = BotGenerator()

#
@main_bp.route('/')
def index():
    templates = [
        {'code': 'make', 'name': 'Запись на услуги', 'desc': 'Для салонов красоты, барбершопов', 'icon': '💅'},
        {'code': 'shop', 'name': 'Интернет-магазин', 'desc': 'Продажа товаров с корзиной', 'icon': '🛍️'},
        {'code': 'quiz', 'name': 'Квиз-бот', 'desc': 'Тесты и викторины с подсчетом баллов', 'icon': '🎯'},
        {'code': 'survey', 'name': 'Опросник', 'desc': 'Сбор обратной связи', 'icon': '📋'},
        {'code': 'mailer', 'name': 'Рассыльщик', 'desc': 'Рассылка новостей', 'icon': '📢'},
    ]
    return render_template('index.html', templates=templates)


@main_bp.route('/choose-platform')
def choose_platform():
    return render_template('choose_platform.html')


@main_bp.route('/instructions')
def instructions():
    return render_template('instructions.html')


@main_bp.route('/choose-template/<platform>')
def choose_template(platform):
    templates = [
        {'code': 'make', 'name': 'Запись на услуги', 'desc': 'Для салонов красоты', 'icon': '💅'},
        {'code': 'shop', 'name': 'Интернет-магазин', 'desc': 'Продажа товаров', 'icon': '🛍️'},
        {'code': 'quiz', 'name': 'Квиз-бот', 'desc': 'Тесты и викторины', 'icon': '🎯'},
        {'code': 'survey', 'name': 'Опросник', 'desc': 'Сбор обратной связи', 'icon': '📋'},
        {'code': 'mailer', 'name': 'Рассыльщик', 'desc': 'Рассылка новостей', 'icon': '📢'},
    ]
    return render_template('choose_template.html', platform=platform, templates=templates)


@main_bp.route('/create/<platform>/<bot_type>')
def create_bot_form(platform, bot_type):
    if not platform or not bot_type:
        flash('Ошибка: не указана платформа или тип бота', 'danger')
        return redirect(url_for('main.choose_platform'))

    template_info = generator.get_template_info(platform, bot_type)
    if not template_info:
        flash(f'Шаблон для {platform}/{bot_type} не найден', 'danger')
        return redirect(url_for('main.choose_template', platform=platform))
    return render_template(
        f'create/platforms/{platform}_base.html',
        bot_type=bot_type,
        template_info=template_info
    )


@main_bp.route('/create', methods=['POST'])
@login_required
def create_bot():
    platform = request.form.get('platform')
    bot_type = request.form.get('bot_type')
    bot_name = request.form.get('bot_name')

    if not all([platform, bot_type, bot_name]):
        flash('Заполните все обязательные поля', 'danger')
        return redirect(url_for('main.choose_platform'))

    if platform == 'tg' and not request.form.get('bot_token'):
        flash('Введите токен бота', 'danger')
        return redirect(url_for('main.create_bot_form', platform=platform, bot_type=bot_type))

    if platform == 'vk' and (not request.form.get('vk_token') or not request.form.get('group_id')):
        flash('Заполните токен сообщества и ID группы', 'danger')
        return redirect(url_for('main.create_bot_form', platform=platform, bot_type=bot_type))

    if platform == 'max' and (not request.form.get('max_key') or not request.form.get('bot_id')):
        flash('Заполните API ключ и ID бота', 'danger')
        return redirect(url_for('main.create_bot_form', platform=platform, bot_type=bot_type))

    if not current_user.is_authenticated:
        flash('Пожалуйста, войдите в систему', 'danger')
        return redirect(url_for('auth.login'))

    user = current_user

    bot = Bot(user_id=user.id, name=bot_name, bot_type=bot_type, platform=platform, token=request.form.get('bot_token') or request.form.get('vk_token') or request.form.get('max_key', ''))
    db.session.add(bot)
    db.session.commit()

    if platform == 'tg' and bot.token:
        try:
            import requests
            response = requests.get(f"https://api.telegram.org/bot{bot.token}/getMe")
            if response.status_code == 200:
                data = response.json()
                if data['ok']:
                    bot.username = data['result']['username']
                    db.session.commit()
        except:
            pass

    config = collect_config_from_form(request.form, platform, bot_type)

    success, message, bot_path = generator.generate_bot(platform=platform, bot_type=bot_type, bot_id=bot.id, config=config)

    if success:
        bot.status = 'generated'
        db.session.commit()

        flash(f'✅ Бот "{bot_name}" успешно создан!', 'success')

        return redirect(url_for('main.list_bots'))
    else:
        flash(f'❌ Ошибка: {message}', 'danger')
        return redirect(url_for('main.list_bots'))


@main_bp.route('/download_temp/<int:bot_id>')
@login_required
def download_temp_bot(bot_id):
    bot = Bot.query.get_or_404(bot_id)

    if bot.user_id != current_user.id:
        flash('❌ У вас нет доступа к этому боту', 'danger')
        return redirect(url_for('main.list_bots'))

    bot_path = bot.folder_path

    if not os.path.exists(bot_path):
        flash('❌ Папка с ботом не найдена', 'danger')
        return redirect(url_for('main.list_bots'))

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(bot_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, bot_path)
                zip_file.write(file_path, arcname)

    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'{bot.name}_{bot.platform}_{bot.id}.zip'
    )


def collect_config_from_form(form_data, platform, bot_type):
    config = {
        'bot_type': bot_type,
        'name': form_data.get('bot_name'),
        'admin_id': form_data.get('admin_id', '6496349641'),
    }

    if platform == 'tg':
        config['token'] = form_data.get('bot_token')
    elif platform == 'vk':
        config['token'] = form_data.get('vk_token')
        config['group_id'] = form_data.get('group_id')
    elif platform == 'max':
        config['api_key'] = form_data.get('max_key')
        config['bot_id'] = form_data.get('bot_id')
        config['secret_key'] = form_data.get('secret_key', '')
        config['webhook_url'] = form_data.get('webhook_url', '')


    if form_data.get('use_sheets') == 'true':
        config['sheet_url'] = form_data.get('sheet_url')
        config['creds_file'] = f'creds_{platform}_{bot_type}.json'
    if bot_type == 'make':
        config.update(collect_make_data(form_data))
    elif bot_type == 'shop':
        config.update(collect_shop_data(form_data))
    elif bot_type == 'quiz':
        config.update(collect_quiz_data(form_data))
    elif bot_type == 'survey':
        config.update(collect_survey_data(form_data))
    elif bot_type == 'mailer':
        config.update(collect_mailer_data(form_data))
    return config


def collect_make_data(form_data):
    masters = []
    names = form_data.getlist('master_name[]')
    emojis = form_data.getlist('master_emoji[]')
    descs = form_data.getlist('master_desc[]')
    specialties = form_data.getlist('master_specialty[]')
    photos = form_data.getlist('master_photo[]')
    for i, name in enumerate(names):
        if name.strip():
            masters.append({
                'id': i + 1,
                'name': name,
                'emoji': emojis[i] if i < len(emojis) else '👤',
                'desc': descs[i] if i < len(descs) else '',
                'specialty': specialties[i] if i < len(specialties) else '',
                'photo': photos[i] if i < len(photos) else None,
            })
    services = []
    service_names = form_data.getlist('service_name[]')
    service_prices = form_data.getlist('service_price[]')
    service_durations = form_data.getlist('service_duration[]')
    service_descs = form_data.getlist('service_desc[]')
    for i, name in enumerate(service_names):
        if name.strip():
            services.append({
                'id': i + 1,
                'name': name,
                'price': service_prices[i] if i < len(service_prices) else 0,
                'duration': service_durations[i] if i < len(service_durations) else 60,
                'desc': service_descs[i] if i < len(service_descs) else ''
            })
    available_times = form_data.get('available_times', '10:00\n11:00\n12:00').split('\n')
    available_times = [t.strip() for t in available_times if t.strip()]
    return {
        'masters': masters,
        'services': services,
        'salon_settings': {
            'name': form_data.get('shop_name', 'Салон красоты'),
            'address': form_data.get('address', 'г. Омск, ул. Масленникова, д. 45'),
            'phone': form_data.get('phone', '+7 (905) 190-01-54'),
            'working_hours': form_data.get('working_hours', 'Пн-Пт: 10:00-20:00, Сб-Вс: 11:00-18:00'),
            'admin_chat_id': form_data.get('admin_id', '6496349641')
        },
        'available_times': available_times,
        'booking_days': int(form_data.get('booking_days', 7)),
        'messages': get_default_messages('make')
    }


def collect_shop_data(form_data):
    categories = []
    cat_names = form_data.getlist('category_name[]')
    cat_emojis = form_data.getlist('category_emoji[]')
    for i, name in enumerate(cat_names):
        if name.strip():
            categories.append({
                'id': i + 1,
                'name': name,
                'emoji': cat_emojis[i] if i < len(cat_emojis) else '📦'
            })
    products = []
    prod_names = form_data.getlist('product_name[]')
    prod_prices = form_data.getlist('product_price[]')
    prod_cats = form_data.getlist('product_category[]')
    prod_descs = form_data.getlist('product_desc[]')
    prod_photos = form_data.getlist('product_photo[]')
    for i, name in enumerate(prod_names):
        if name.strip():
            products.append({
                'id': i + 1,
                'category_id': int(prod_cats[i]) if i < len(prod_cats) else 1,
                'name': name,
                'price': int(prod_prices[i]) if i < len(prod_prices) else 0,
                'desc': prod_descs[i] if i < len(prod_descs) else '',
                'photo': prod_photos[i] if i < len(prod_photos) else None
            })
    return {
        'categories': categories,
        'products': products,
        'shop_settings': {
            'name': form_data.get('shop_name', 'Мой магазин'),
            'currency': form_data.get('currency', '₽'),
            'delivery_available': form_data.get('delivery_available') == 'true',
            'admin_chat_id': form_data.get('admin_id', '6496349641')
        },
        'messages': get_default_messages('shop')
    }


def collect_quiz_data(form_data):
    quizzes = []

    quiz_names = form_data.getlist('quiz_name[]')
    quiz_descs = form_data.getlist('quiz_desc[]')

    all_question_texts = form_data.getlist('question_text[]')
    all_question_options = form_data.getlist('question_options[]')
    all_question_points = form_data.getlist('question_points[]')
    all_result_types = form_data.getlist('result_type[]')
    all_result_texts = form_data.getlist('result_text[]')
    all_result_min_scores = form_data.getlist('result_min_score[]')

    num_quizzes = len(quiz_names)
    if num_quizzes == 0:
        return {'quizzes': [], 'messages': get_default_messages('quiz')}

    questions_per_quiz = len(all_question_texts) // num_quizzes if num_quizzes > 0 else 0
    results_per_quiz = len(all_result_types) // num_quizzes if num_quizzes > 0 else 0

    for quiz_idx in range(num_quizzes):
        questions = []
        start_q = quiz_idx * questions_per_quiz
        end_q = start_q + questions_per_quiz

        for i in range(start_q, end_q):
            if i < len(all_question_texts) and all_question_texts[i].strip():
                options_text = all_question_options[i] if i < len(all_question_options) else ''
                options_lines = [line.strip() for line in options_text.split('\n') if line.strip()]

                points_text = all_question_points[i] if i < len(all_question_points) else ''
                points_list = [p.strip() for p in points_text.split(',') if p.strip()]

                options = []
                for j, option_text in enumerate(options_lines):
                    point_value = int(points_list[j]) if j < len(points_list) else 0
                    options.append({
                        'text': option_text,
                        'points': {f"q{quiz_idx + 1}_opt{j + 1}": point_value}
                    })

                questions.append({
                    'id': i + 1,
                    'text': all_question_texts[i],
                    'options': options
                })

        results = []
        start_r = quiz_idx * results_per_quiz
        end_r = start_r + results_per_quiz

        for i in range(start_r, end_r):
            if i < len(all_result_types) and all_result_types[i].strip():
                min_score = int(all_result_min_scores[i]) if i < len(all_result_min_scores) else 0
                results.append({
                    'type': all_result_types[i].strip(),
                    'text': all_result_texts[i] if i < len(all_result_texts) else '',
                    'min_score': min_score
                })
        results.sort(key=lambda x: x['min_score'], reverse=True)

        quizzes.append({
            'id': quiz_idx + 1,
            'name': quiz_names[quiz_idx] if quiz_idx < len(quiz_names) else f'Квиз {quiz_idx + 1}',
            'description': quiz_descs[quiz_idx] if quiz_idx < len(quiz_descs) else '',
            'questions': questions,
            'results': results
        })

    return {
        'quizzes': quizzes,
        'messages': get_default_messages('quiz')
    }


def collect_survey_data(form_data):
    surveys = []

    survey_names = form_data.getlist('survey_name[]')
    survey_descs = form_data.getlist('survey_desc[]')
    survey_anonymous = form_data.getlist('survey_anonymous[]')

    #получаем все вопросы
    all_question_texts = form_data.getlist('question_text[]')
    all_question_types = form_data.getlist('question_type[]')
    all_question_options = form_data.getlist('question_options[]')
    all_scale_min = form_data.getlist('scale_min[]')
    all_scale_max = form_data.getlist('scale_max[]')

    num_surveys = len(survey_names)
    if num_surveys == 0:
        return {'surveys': [], 'survey_settings': {}, 'messages': get_default_messages('survey')}

    questions_per_survey = len(all_question_texts) // num_surveys if num_surveys > 0 else 0

    for survey_idx in range(num_surveys):
        questions = []
        start_q = survey_idx * questions_per_survey
        end_q = start_q + questions_per_survey

        for i in range(start_q, end_q):
            if i < len(all_question_texts) and all_question_texts[i].strip():
                question = {
                    'id': i + 1,
                    'type': all_question_types[i] if i < len(all_question_types) else 'text',
                    'text': all_question_texts[i]
                }

                if question['type'] in ['single', 'multiple']:
                    options_text = all_question_options[i] if i < len(all_question_options) else ''
                    question['options'] = [line.strip() for line in options_text.split('\n') if line.strip()]

                if question['type'] == 'scale':
                    min_val = int(all_scale_min[i]) if i < len(all_scale_min) else 1
                    max_val = int(all_scale_max[i]) if i < len(all_scale_max) else 5
                    if min_val < 1:
                        min_val = 1
                    if max_val > 5:
                        max_val = 5
                    if min_val >= max_val:
                        max_val = min_val + 1
                    question['min'] = min_val
                    question['max'] = max_val

                questions.append(question)

        surveys.append({
            'id': survey_idx + 1,
            'name': survey_names[survey_idx] if survey_idx < len(survey_names) else f'Опрос {survey_idx + 1}',
            'description': survey_descs[survey_idx] if survey_idx < len(survey_descs) else '',
            'questions': questions,
            'anonymous': survey_anonymous[survey_idx] == 'true' if survey_idx < len(survey_anonymous) else False
        })

    return {
        'surveys': surveys,
        'survey_settings': {
            'name': 'Опросник-бот',
            'admin_chat_id': form_data.get('admin_id', '6496349641'),
            'allow_anonymous': form_data.get('anonymous') == 'true'
        },
        'messages': get_default_messages('survey')
    }


def collect_mailer_data(form_data):
    groups = []
    group_names = form_data.getlist('group_name[]')
    for i, name in enumerate(group_names):
        if name.strip():
            groups.append({
                'id': i + 1,
                'name': name
            })
    if not groups:
        groups = [{'id': 1, 'name': 'Все подписчики'}]
    return {
        'mailer_settings': {
            'name': form_data.get('mailer_name', 'Рассыльщик'),
            'admin_chat_id': form_data.get('admin_id', '6496349641'),
            'subscribe_on_start': form_data.get('subscribe_on_start') == 'true',
            'welcome_message': form_data.get('welcome_message', '👋 Добро пожаловать!')
        },
        'groups': groups,
        'messages': get_default_messages('mailer')
    }


def get_default_messages(bot_type):
    messages = {
        'make': {
            'welcome': '💅 *Добро пожаловать в {name}!*\n\nЯ помогу вам записаться. Выберите действие:',
            'choose_master': '👩‍🎨 *Выберите мастера:*',
            'choose_date': '📅 *Выберите дату:*',
            'choose_time': '🕐 *Выберите время:*',
            'enter_name': '📝 *Введите ваше имя:*',
            'enter_phone': '📞 *Введите ваш телефон:*',
            'enter_comment': '💬 *Добавьте комментарий (если нужно):*\nИли отправьте \'-\'',
            'booking_success': '✅ *Запись успешно оформлена!*\n\n• Мастер: {master}\n• Дата: {date}\n• Время: {time}\n• Телефон: {phone}',
            'booking_error': '😔 *Ошибка при записи*\n\nПопробуйте позже или позвоните нам {phone}',
            'my_bookings': '📋 *Ваши записи:*\n\n{bookings}',
            'no_bookings': '📭 *У вас пока нет записей*',
            'about': 'ℹ️ *О салоне*\n\n{address}\n🕐 {hours}\n📞 {phone}',
            'contacts': '📞 *Контакты*\n\n📍 {address}\n🕐 {hours}\n📞 {phone}'
        },
        'shop': {
            'welcome': '🛍 *Добро пожаловать в {name}!*\n\nВыберите действие:',
            'catalog': '📋 *Выберите категорию:*',
            'product_info': '🛍 *{name}*\n\n💰 Цена: *{price}{currency}*\n📝 {desc}',
            'cart_empty': '🛒 *Ваша корзина пуста*',
            'cart': '🛒 *Ваша корзина:*\n\n{cart}\n💰 *Итого: {total}{currency}*',
            'ask_name': '📝 *Введите ваше имя:*',
            'ask_phone': '📞 *Введите ваш телефон:*',
            'ask_address': '📍 *Введите адрес доставки:*',
            'order_success': '✅ *Заказ успешно оформлен!*\n\n{order_details}\n\nСпасибо за покупку!'
        },
        'quiz': {
            'welcome': '🎯 *Добро пожаловать в мир квизов!*\n\nВыберите интересующий вас тест:',
            'quiz_start': '📝 *{name}*\n\n{description}\n\nВсего вопросов: {questions}',
            'question': '❓ *Вопрос {current}/{total}*\n\n{text}',
            'result': '🎉 *Ваш результат:*\n\n{result}',
            'no_quizzes': '📭 Пока нет доступных квизов',
            'my_results': '📊 *Мои результаты:*\n\n{results}',
            'no_results': '📭 Вы еще не проходили квизы'
        },
        'survey': {
            'welcome': '📋 *Добро пожаловать!*\n\nЗдесь вы можете пройти опросы и поделиться своим мнением.',
            'surveys_list': '📋 *Доступные опросы:*',
            'no_surveys': '📭 Пока нет доступных опросов',
            'survey_start': '📝 *{name}*\n\n{description}\n\nВсего вопросов: {questions}\n\n*Начать опрос?*',
            'question_text': '📝 *Вопрос {current}/{total}*\n\n{text}',
            'question_single': '📝 *Вопрос {current}/{total}*\n\n{text}\n\nВыберите один вариант:',
            'question_multiple': '📝 *Вопрос {current}/{total}*\n\n{text}\n\nВыберите несколько вариантов:',
            'question_scale': '📝 *Вопрос {current}/{total}*\n\n{text}\n\nОцените от {min} до {max}:',
            'thanks': '🙏 *Спасибо за участие в опросе!*',
            'my_surveys': '📋 *Мои пройденные опросы:*\n\n{surveys}',
            'no_surveys_taken': '📭 Вы еще не проходили опросы'
        },
        'mailer': {
            'welcome': '📢 *Добро пожаловать в бот-рассыльщик!*\n\nЗдесь вы можете подписаться на новости.',
            'subscribed': '✅ Вы успешно подписались на рассылку!',
            'unsubscribed': '❌ Вы отписались от рассылки. Будем ждать вас снова!',
            'already_subscribed': 'ℹ️ Вы уже подписаны на рассылку',
            'not_subscribed': 'ℹ️ Вы не подписаны на рассылку',
            'stats': '📊 *Статистика*\n\n👥 Всего подписчиков: {total}\n✅ Активных: {active}',
            'mailing_start': '📨 Рассылка начата. Отправлено: {sent} | Ошибок: {failed}',
            'mailing_complete': '✅ Рассылка завершена!\n\nВсего: {total}\n✅ Доставлено: {sent}\n❌ Ошибок: {failed}'
        }
    }
    return messages.get(bot_type, {})


@main_bp.route('/bots')
@login_required
def list_bots():
    bots = Bot.query.filter_by(user_id=current_user.id).all()
    return render_template('bots.html', bots=bots)


@main_bp.route('/bot/<int:bot_id>/delete', methods=['POST'])
@login_required
def delete_bot(bot_id):
    bot = Bot.query.get_or_404(bot_id)
    if bot.user_id != current_user.id:
        flash('❌ У вас нет доступа к этому боту', 'danger')
        return redirect(url_for('main.list_bots'))
    bot_path = os.path.join('bots', 'generated', f'{bot.platform}_{bot.id}')
    if os.path.exists(bot_path):
        import shutil
        shutil.rmtree(bot_path)
    db.session.delete(bot)
    db.session.commit()
    flash(f'Бот {bot.name} удален', 'success')
    return redirect(url_for('main.list_bots'))


@main_bp.route('/bot/<int:bot_id>/restart', methods=['POST'])
@login_required
def restart_bot(bot_id):
    bot = Bot.query.get_or_404(bot_id)
    flash(f'Бот {bot.name} перезапущен', 'success')
    return redirect(url_for('main.list_bots'))


@main_bp.route('/api/template-info/<platform>/<bot_type>')
def api_template_info(platform, bot_type):
    info = generator.get_template_info(platform, bot_type)
    return jsonify(info)

@main_bp.route('/test-pay')
def test_pay():
    return render_template('test_payment.html')

