from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def permission_required(permission_name):
    """Checks if the current user has the required permission."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('يرجى تسجيل الدخول للوصول إلى هذه الصفحة', 'warning')
                return redirect(url_for('auth.login'))
            if not current_user.has_permission(permission_name):
                flash('ليس لديك الصلاحية الكافية للوصول إلى هذه الصفحة.', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator