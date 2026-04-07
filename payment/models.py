from datetime import datetime
from app.extensions import db


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bot_id = db.Column(db.Integer, db.ForeignKey('bots.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='RUB')
    status = db.Column(db.String(20), default='pending')
    payment_id = db.Column(db.String(100), unique=True)
    payment_method = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)
    payment_data = db.Column(db.Text)

    user = db.relationship('User', backref='payments')
    bot = db.relationship('Bot', backref='payment')


class PriceList(db.Model):
    __tablename__ = 'price_list'

    id = db.Column(db.Integer, primary_key=True)
    bot_type = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)

    @classmethod
    def get_price(cls, bot_type):
        item = cls.query.filter_by(bot_type=bot_type).first()
        return item.price if item else 0