import time
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse

from hotel import db, csrf
from hotel.models.user import User
from hotel.forms.auth import LoginForm, RegistrationForm, ChangePasswordForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
@csrf.exempt
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
            return redirect(url_for('auth.login'))

        # Force non-remembered session so it ends when the browser closes
        login_user(user, remember=False)
        # Track last activity for server-side inactivity logout
        session.permanent = False
        session['last_activity'] = int(time.time())
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)

    return render_template('auth/login.html', title='تسجيل الدخول', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    # Logout and clear all session data
    logout_user()
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('main.index'))



@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('كلمة المرور الحالية غير صحيحة', 'danger')
            return redirect(url_for('auth.change_password'))

        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('تم تغيير كلمة المرور بنجاح', 'success')
        return redirect(url_for('main.index'))

    return render_template('auth/change_password.html', title='تغيير كلمة المرور', form=form)
