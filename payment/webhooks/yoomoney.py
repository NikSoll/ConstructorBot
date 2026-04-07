from flask import request, jsonify
from payment import payment_bp
from payment.models import Payment
from payment.yoomoney import yoomoney
from app.extensions import db
from datetime import datetime
import logging


@payment_bp.route('/webhook/yoomoney', methods=['POST'])
def yoomoney_webhook():
    logger = logging.getLogger(__name__)

    try:
        data = request.json

        if not data:
            logger.error("No data received")
            return jsonify({'error': 'No data'}), 400

        result = yoomoney.process_webhook(data)

        if not result:
            return jsonify({'error': 'Invalid notification'}), 400

        payment = Payment.query.filter_by(payment_id=result['payment_id']).first()

        if not payment:
            logger.error(f"Payment not found: {result['payment_id']}")
            return jsonify({'error': 'Payment not found'}), 404

        if result['status'] == 'succeeded':
            payment.status = 'paid'
            payment.paid_at = datetime.utcnow()

            if payment.bot:
                payment.bot.status = 'active'

            logger.info(f"Payment {payment.id} completed successfully")

        elif result['status'] == 'canceled':
            payment.status = 'failed'
            logger.info(f"Payment {payment.id} was canceled")

        db.session.commit()

        return jsonify({'status': 'ok'}), 200

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 500