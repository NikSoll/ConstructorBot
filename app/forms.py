from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models import User


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[
        DataRequired(message='Введите email'),
        Email(message='Введите корректный email')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Введите пароль'),
        Length(min=6, message='Пароль должен быть минимум 6 символов')
    ])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[
        DataRequired(message='Введите имя'),
        Length(min=2, max=50, message='Имя должно быть от 2 до 50 символов')
    ])
    email = EmailField('Email', validators=[
        DataRequired(message='Введите email'),
        Email(message='Введите корректный email')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Введите пароль'),
        Length(min=6, message='Пароль должен быть минимум 6 символов')
    ])
    password2 = PasswordField('Повторите пароль', validators=[
        DataRequired(message='Повторите пароль'),
        EqualTo('password', message='Пароли не совпадают')
    ])
    submit = SubmitField('Зарегистрироваться')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Этот email уже зарегистрирован')


class ProfileForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[
        DataRequired(message='Введите имя'),
        Length(min=2, max=50, message='Имя должно быть от 2 до 50 символов')
    ])
    email = EmailField('Email', validators=[
        DataRequired(message='Введите email'),
        Email(message='Введите корректный email')
    ])
    current_password = PasswordField('Текущий пароль')
    new_password = PasswordField('Новый пароль', validators=[
        Length(min=6, message='Пароль должен быть минимум 6 символов')
    ])
    confirm_password = PasswordField('Подтвердите пароль', validators=[
        EqualTo('new_password', message='Пароли не совпадают')
    ])
    submit = SubmitField('Сохранить')