import os
import time
from datetime import datetime, timedelta
from flask import Flask, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)

    # Configure app
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///instance/hotel.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # Use non-permanent session cookies so they expire when the browser closes
    app.config['SESSION_PERMANENT'] = False
    # Keep inactivity timeout server-side as an extra safety net
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)
    
    # إعدادات التشفير لحل مشكلة النصوص العربية
    app.config['JSON_AS_ASCII'] = False
    app.config['JSON_SORT_KEYS'] = False

    # تحسينات الأداء
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'timeout': 20,
            'check_same_thread': False
        }
    }

    # إعدادات الأداء العامة
    # تعطيل التخزين المؤقت للملفات الثابتة أثناء التطوير لضمان تحميل التغييرات فورًا
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # حد أقصى 20MB لكل طلب
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['EXPLAIN_TEMPLATE_LOADING'] = False
    
    # إعدادات إضافية لإزالة قيود الرفع
    app.config['MAX_FORM_MEMORY_SIZE'] = 20 * 1024 * 1024  # حد أقصى 20MB لكل نموذج
    app.config['MAX_FORM_PARTS'] = None  # إزالة حد أجزاء النموذج

    # منع انتهاء صلاحية CSRF token أثناء الانتظار أو إعادة المحاولة
    app.config['WTF_CSRF_TIME_LIMIT'] = None

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Configure login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'الرجاء تسجيل الدخول للوصول إلى هذه الصفحة'
    login_manager.login_message_category = 'info'

    # Inactivity timeout: auto-logout after 10 minutes of no activity
    @app.before_request
    def enforce_inactivity_timeout():
        from flask_login import current_user, logout_user
        # allow login/logout and static without checks to avoid loops
        allowed_endpoints = {'auth.login', 'auth.logout', 'static'}
        if request.endpoint in allowed_endpoints:
            return
        if current_user.is_authenticated:
            now_ts = int(time.time())
            last_ts = session.get('last_activity', now_ts)
            if now_ts - last_ts > 600:  # 10 minutes
                logout_user()
                session.clear()
                flash('تم تسجيل خروجك تلقائيًا بسبب عدم النشاط لمدة 10 دقائق', 'warning')
                return redirect(url_for('auth.login'))
            # update last activity timestamp on each request
            session['last_activity'] = now_ts

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from hotel.models.user import User
        return User.query.get(int(user_id))

    # Register blueprints
    from hotel.routes.main import main_bp
    from hotel.routes.auth import auth_bp
    from hotel.routes.admin import admin_bp
    from hotel.routes.user import user_bp
    from hotel.routes.room import room_bp
    from hotel.routes.booking import booking_bp
    from hotel.routes.booking_guest import booking_guest_bp
    from hotel.routes.customer import customer_bp
    from hotel.routes.customer_new import customer_new_bp
    from hotel.routes.payment import payment_bp
    from hotel.routes.reports import reports_bp
    from hotel.routes.room_transfer import room_transfer_bp
    from hotel.routes.api import api_bp
    from hotel.routes.notes import notes_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(room_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(booking_guest_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(customer_new_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(room_transfer_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(notes_bp)

    # Register custom Jinja2 filters
    from hotel.utils.datetime_utils import egypt_datetime
    app.jinja_env.filters['egypt_datetime'] = egypt_datetime
    
    # Add context processor for templates
    @app.context_processor
    def inject_now():
        from hotel.utils.datetime_utils import get_egypt_now
        return {'now': get_egypt_now()}

    @app.context_processor
    def inject_static_version():
        # Cache-busting for static files
        return {'static_version': int(time.time())}

    @app.context_processor
    def inject_note_counters():
        """حقن عداد الملاحظات غير المنجزة للمستخدم الحالي."""
        count = 0
        try:
            from flask_login import current_user
            from hotel.models.note import Note, NOTE_STATUS_PENDING
            if current_user.is_authenticated:
                count = Note.query.filter_by(receiver_id=current_user.id, status=NOTE_STATUS_PENDING).count()
        except Exception:
            # في حال عدم توفر قاعدة البيانات أثناء الإقلاع
            count = 0
        return {'pending_notes_count': count}

    # Add custom template filters
    from hotel.utils.arabic_date import get_arabic_date, format_date_simple
    from hotel.utils.template_filters import register_template_filters

    # تسجيل الدوال المساعدة للقوالب
    register_template_filters(app)

    @app.template_filter('arabic_date')
    def arabic_date_filter(date_obj):
        """تحويل التاريخ إلى عربي"""
        return get_arabic_date(date_obj)

    @app.template_filter('arabic_date_simple')
    def arabic_date_simple_filter(date_obj):
        """تحويل التاريخ إلى عربي بسيط"""
        return format_date_simple(date_obj)

    # Error handlers - تم إزالة معالج خطأ 413 لأنه لا يوجد حد أقصى للحجم الآن

    # Create database tables and initial data
    with app.app_context():
        try:
            db.create_all()
            create_initial_permissions()
        except Exception as e:
            print(f"Warning: Could not create database tables or initial data: {e}")

    return app

def create_initial_permissions():
    from hotel.models import Permission
    # Initial permissions
    permissions = [
        {'name': 'admin', 'description': 'إدارة كاملة للنظام'},
        {'name': 'dashboard', 'description': 'الوصول إلى لوحة التحكم'},
        {'name': 'manage_users', 'description': 'إدارة المستخدمين'},
        {'name': 'manage_rooms', 'description': 'إدارة الغرف'},
        {'name': 'manage_bookings', 'description': 'إدارة الحجوزات'},
        {'name': 'manage_customers', 'description': 'إدارة العملاء'},
        {'name': 'manage_payments', 'description': 'إدارة المدفوعات'},
        {'name': 'view_reports', 'description': 'عرض التقارير'},
        {'name': 'delete_data', 'description': 'حذف البيانات'},
        {'name': 'create_booking', 'description': 'إنشاء حجز جديد'},
        {'name': 'edit_booking', 'description': 'تعديل الحجوزات'},
        {'name': 'delete_booking', 'description': 'حذف الحجوزات'},
        {'name': 'check_in_out', 'description': 'تسجيل الدخول والخروج'},
        {'name': 'add_payment', 'description': 'إضافة دفعة جديدة'},
        {'name': 'edit_payment', 'description': 'تعديل الدفعات'},
        {'name': 'delete_payment', 'description': 'حذف الدفعات'},
        {'name': 'transfer_room', 'description': 'نقل الغرف'},
        {'name': 'manage_deus', 'description': 'إدارة حجوزات الديوز'},
    ]

    for perm_data in permissions:
        permission = Permission.query.filter_by(name=perm_data['name']).first()
        if not permission:
            permission = Permission(name=perm_data['name'], description=perm_data['description'])
            db.session.add(permission)
        else:
            # تحديث الوصف إذا كان مختلف
            if permission.description != perm_data['description']:
                permission.description = perm_data['description']

    db.session.commit()

    # التأكد من أن المستخدم admin لديه صلاحية admin
    from hotel.models import User
    admin_user = User.query.filter_by(username='admin').first()
    admin_permission = Permission.query.filter_by(name='admin').first()

    if admin_user and admin_permission and admin_permission not in admin_user.permissions:
        admin_user.permissions.append(admin_permission)
        db.session.commit()