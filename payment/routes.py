from flask import render_template, request, jsonify, current_app, url_for, flash, redirect
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Bot
from payment import payment_bp
from payment.models import Payment, PriceList
from payment.yoomoney import yoomoney
import json
from datetime import datetime


@payment_bp.route('/checkout/<int:bot_id>')
@login_required
def checkout(bot_id):
    bot = Bot.query.get_or_404(bot_id)

    if bot.user_id != current_user.id:
        flash('❌ У вас нет доступа к этому боту', 'danger')
        return redirect(url_for('main.index'))

    price_item = PriceList.query.filter_by(bot_type=bot.bot_type).first()
    if not price_item:
        flash('❌ Цена для этого типа бота не установлена', 'danger')
        return redirect(url_for('main.list_bots'))

    existing_payment = Payment.query.filter_by(
        bot_id=bot_id,
        status='paid'
    ).first()

    if existing_payment:
        flash('✅ Этот бот уже оплачен', 'success')
        #еще маршрут для скач
        return redirect(url_for('main.list_bots'))

    return render_template(
        'payment/checkout.html',
        bot=bot,
        price=price_item.price,
        bot_type_name=price_item.name
    )


@payment_bp.route('/create', methods=['POST'])
@login_required
def create_payment():
    bot_id = request.form.get('bot_id')
    print(f"+ create_payment called for bot_id={bot_id}")

    if not bot_id:
        return jsonify({'error': 'Bot ID required'}), 400

    bot = Bot.query.get_or_404(bot_id)
    print(f"+ Bot found: {bot.name}")

    if bot.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    price = PriceList.get_price(bot.bot_type)
    print(f"+ Price: {price}")

    if price <= 0:
        return jsonify({'error': 'Invalid price'}), 400

    payment_record = Payment(
        user_id=current_user.id,
        bot_id=bot.id,
        amount=price,
        status='pending',
        payment_data=json.dumps({
            'bot_name': bot.name,
            'bot_type': bot.bot_type,
            'platform': bot.platform,
            'user_email': current_user.email
        })
    )
    db.session.add(payment_record)
    db.session.commit()
    print(f"+ Payment record created: {payment_record.id}")

    description = f'Оплата бота "{bot.name}" ({price}₽)'
    payment_data = {
        'payment_id': payment_record.id,
        'user_id': current_user.id,
        'bot_id': bot.id,
        'email': current_user.email
    }

    try:
        print("+ Calling yoomoney.create_payment...")
        payment = yoomoney.create_payment(price, description, payment_data)
        print(f"+ Payment response: {payment}")

        if payment and payment.confirmation:
            payment_record.payment_id = payment.id
            db.session.commit()
            print(f"+ Payment created, redirecting to {payment.confirmation.confirmation_url}")
            return redirect(payment.confirmation.confirmation_url)
        else:
            print("+ Payment creation failed - no confirmation URL")
            flash('❌ Ошибка при создании платежа: нет подтверждения', 'danger')
            return redirect(url_for('payment.checkout', bot_id=bot_id))

    except Exception as e:
        print(f"+ Exception in create_payment: {e}")
        import traceback
        traceback.print_exc()
        flash(f'❌ Ошибка при создании платежа: {str(e)}', 'danger')
        return redirect(url_for('payment.checkout', bot_id=bot_id))

@payment_bp.route('/success')
@login_required
def success():
    return render_template('payment/success.html')


@payment_bp.route('/fail')
@login_required
def fail():
    return render_template('payment/fail.html')


@payment_bp.route('/history')
@login_required
def history():
    payments = Payment.query.filter_by(
        user_id=current_user.id
    ).order_by(Payment.created_at.desc()).all()

    return render_template('payment/history.html', payments=payments)