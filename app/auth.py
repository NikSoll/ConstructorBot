from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User
from app.forms import LoginForm, RegistrationForm, ProfileForm
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()

            flash(f'👋 С возвращением, {user.username}!', 'success')

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.index'))
        else:
            flash('❌ Неверный email или пароль', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            created_at=datetime.utcnow()
        )

        db.session.add(user)
        db.session.commit()

        flash('✅ Регистрация прошла успешно! Теперь вы можете войти.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('👋 Вы вышли из системы', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        if form.email.data != current_user.email:
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('❌ Этот email уже занят', 'danger')
                return render_template('auth/profile.html', form=form)

        current_user.username = form.username.data
        current_user.email = form.email.data

        if form.new_password.data:
            if not check_password_hash(current_user.password_hash, form.current_password.data):
                flash('❌ Неверный текущий пароль', 'danger')
                return render_template('auth/profile.html', form=form)

            current_user.password_hash = generate_password_hash(form.new_password.data)

        db.session.commit()
        flash('✅ Профиль обновлен', 'success')
        return redirect(url_for('auth.profile'))

    bots_count = len(current_user.bots)
    recent_bots = current_user.bots[-5:]

    return render_template('auth/profile.html',form=form,bots_count=bots_count,recent_bots=recent_bots)


@auth_bp.route('/profile/delete', methods=['POST'])
@login_required
def delete_account():
    user_id = current_user.id

    logout_user()

    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()

    flash('👋 Ваш аккаунт удален. Будем ждать вас снова!', 'info')
    return redirect(url_for('main.index'))