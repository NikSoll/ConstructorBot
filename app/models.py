from datetime import datetime
from app.extensions import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    #UserMixin чтобы были готовые методы для антиф
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    bots = db.relationship('Bot', backref='owner', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'


class Bot(db.Model):
    __tablename__ = 'bots'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    bot_type = db.Column(db.String(20), nullable=False)
    platform = db.Column(db.String(10), nullable=False)
    token = db.Column(db.String(200))
    config_path = db.Column(db.String(500))
    status = db.Column(db.String(20), default='stopped')#пока не будет реализованно хранение на сервере, бесполезно
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_started = db.Column(db.DateTime)
    username = db.Column(db.String(100)) #ссылка на бота, тут косяк, надо исправить. создает только для тг

    def __repr__(self):
        return f'<Bot {self.name} ({self.platform}/{self.bot_type})>'

    @property
    def folder_name(self):
        return f"{self.platform}_{self.id}"

    @property
    def folder_path(self):
        from flask import current_app
        import os
        return os.path.join(current_app.config['BOTS_DIR'], self.folder_name)

    @property
    def bot_link(self):
        if self.platform == 'tg' and self.token:
            return f"https://t.me/{self.token.split(':')[0]}"
        elif self.platform == 'vk':
            return f"https://vk.com/club{self.group_id}" if hasattr(self, 'group_id') else "#"
        elif self.platform == 'max':
            return "#"  #придумаю что-нибудь.... 2 недели спустя... не придумал...
        return "#"