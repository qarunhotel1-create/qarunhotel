from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, make_response
from flask_login import login_required, current_user
from hotel import db
from hotel.models import User, Room, Customer, Booking, Payment
from hotel.utils.decorators import permission_required
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_, func
import json
import logging
import traceback

# إعداد الـ logger على مستوى الموديل
logger = logging.getLogger(__name__)

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@login_required
@permission_required('view_reports')
def index():
    """صفحة التقارير الرئيسية"""
    return render_template('reports/index.html', title='التقارير')

@reports_bp.route('/dashboard')
@login_required
@permission_required('view_reports')
def dashboard():
    """لوحة تحكم التقارير"""
    # إحصائيات بسيطة
    try:
        total_users = User.query.count()
        total_rooms = Room.query.count()
        total_customers = Customer.query.count()
        total_bookings = Booking.query.filter(Booking.status != 'cancelled').count()
        
        # إحصائيات الغرف
        available_rooms = Room.query.filter_by(status='available').count()
        occupied_rooms = Room.query.filter_by(status='occupied').count()
        maintenance_rooms = Room.query.filter_by(status='maintenance').count()
        
        # إحصائيات الحجوزات
        pending_bookings = Booking.query.filter_by(status='pending').count()
        confirmed_bookings = Booking.query.filter_by(status='confirmed').count()
        cancelled_bookings = Booking.query.filter_by(status='cancelled').count()
        
        stats = {
            'general': {
                'total_users': total_users,
                'total_rooms': total_rooms,
                'total_customers': total_customers,
                'total_bookings': total_bookings
            },
            'bookings': {
                'active': 0,
                'pending': pending_bookings,
                'confirmed': confirmed_bookings,
                'cancelled': cancelled_bookings,
                'monthly': 0
            },
            'rooms': {
                'available': available_rooms,
                'occupied': occupied_rooms,
                'maintenance': maintenance_rooms,
                'total': total_rooms
            },

            'users': {
                'admin': User.query.filter(User.permissions.any(name='admin')).count(),
                'manage_users': User.query.filter(User.permissions.any(name='manage_users')).count(),
                'manage_bookings': User.query.filter(User.permissions.any(name='manage_bookings')).count(),
                'manage_payments': User.query.filter(User.permissions.any(name='manage_payments')).count(),
                'view_reports': User.query.filter(User.permissions.any(name='view_reports')).count(),
            }
        }
    except Exception as e:
        # في حالة حدوث خطأ، استخدم قيم افتراضية
        stats = {
            'general': {'total_users': 0, 'total_rooms': 0, 'total_customers': 0, 'total_bookings': 0},
            'bookings': {'active': 0, 'pending': 0, 'confirmed': 0, 'cancelled': 0, 'monthly': 0},
            'rooms': {'available': 0, 'occupied': 0, 'maintenance': 0, 'total': 0},

            'users': {'admin': 0, 'manage_users': 0, 'manage_bookings': 0, 'manage_payments': 0, 'view_reports': 0}
        }
    
    return render_template('reports/dashboard.html', title='لوحة تحكم التقارير', stats=stats)

@reports_bp.route('/bookings')
@login_required
@permission_required('view_reports')
def bookings_report():
    """تقرير الحجوزات"""
    try:
        # الحصول على المعاملات
        page = request.args.get('page', 1, type=int)
        per_page = 25
        status_filter = request.args.get('status', 'all')

        # بناء الاستعلام - استبعاد الحجوزات الملغية من التقارير
        query = Booking.query.join(Customer).join(Room).filter(Booking.status != 'cancelled')

        if status_filter != 'all':
            query = query.filter(Booking.status == status_filter)

        # ترقيم الصفحات
        bookings_pagination = query.order_by(Booking.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        bookings = bookings_pagination.items

        # حساب الإحصائيات
        total_bookings = query.count()
        total_nights = 0
        total_amount = 0

        for booking in bookings:
            if booking.check_in_date and booking.check_out_date:
                nights = (booking.check_out_date - booking.check_in_date).days
                total_nights += nights
            if booking.total_price:
                total_amount += booking.total_price

        stats = {
            'total_bookings': total_bookings,
            'total_nights': total_nights,
            'total_amount': total_amount,
            'average_stay': round(total_nights / total_bookings, 1) if total_bookings > 0 else 0,
            'average_amount': round(total_amount / total_bookings, 2) if total_bookings > 0 else 0
        }

        # إحصائيات الحالات
        status_stats = {
            'pending': Booking.query.filter_by(status='pending').count(),
            'confirmed': Booking.query.filter_by(status='confirmed').count(),
            'checked_in': Booking.query.filter_by(status='checked_in').count(),
            'checked_out': Booking.query.filter_by(status='checked_out').count(),
            'cancelled': Booking.query.filter_by(status='cancelled').count()
        }

    except Exception as e:
        print(f"خطأ في تقرير الحجوزات: {e}")
        bookings = []
        bookings_pagination = None
        stats = {'total_bookings': 0, 'total_nights': 0, 'total_amount': 0, 'average_stay': 0, 'average_amount': 0}
        status_stats = {'pending': 0, 'confirmed': 0, 'checked_in': 0, 'checked_out': 0, 'cancelled': 0}

    # إعداد متغير filters للقالب
    filters = {
        'start_date': request.args.get('start_date'),
        'end_date': request.args.get('end_date'),
        'status': status_filter
    }
    
    return render_template('reports/bookings.html',
                         title='تقرير الحجوزات',
                         bookings=bookings,
                         pagination=bookings_pagination,
                         stats=stats,
                         status_stats=status_stats,
                         current_status=status_filter,
                         filters=filters)

@reports_bp.route('/bookings/pdf')
@login_required
@permission_required('view_reports')
def bookings_report_pdf():
    """تصدير تقرير الحجوزات كـ PDF"""
    try:
        # الحصول على المعاملات
        status_filter = request.args.get('status', 'all')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # بناء الاستعلام - جميع الحجوزات للتصدير (بدون ترقيم صفحات)
        query = Booking.query.join(Customer).join(Room).filter(Booking.status != 'cancelled')
        
        if status_filter != 'all':
            query = query.filter(Booking.status == status_filter)
            
        if start_date:
            from datetime import datetime
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Booking.check_in_date >= start_date_obj)
            
        if end_date:
            from datetime import datetime
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Booking.check_out_date <= end_date_obj)
        
        bookings = query.order_by(Booking.created_at.desc()).all()
        
        # حساب الإحصائيات
        total_bookings = len(bookings)
        total_nights = 0
        total_amount = 0
        
        for booking in bookings:
            if booking.check_in_date and booking.check_out_date:
                nights = (booking.check_out_date - booking.check_in_date).days
                total_nights += nights
            if booking.total_price:
                total_amount += booking.total_price
        
        stats = {
            'total_bookings': total_bookings,
            'total_nights': total_nights,
            'total_amount': total_amount,
            'average_stay': round(total_nights / total_bookings, 1) if total_bookings > 0 else 0,
            'average_amount': round(total_amount / total_bookings, 2) if total_bookings > 0 else 0
        }
        
        # إعداد متغير filters للـ PDF
        filters = {
            'start_date': start_date,
            'end_date': end_date,
            'status': status_filter
        }
        
        # إنشاء تقرير PDF
        return generate_pdf_report(bookings, stats, filters, report_type='bookings')
        
    except Exception as e:
        logger.error(f"خطأ في تصدير تقرير الحجوزات PDF: {e}")
        flash('حدث خطأ أثناء تصدير التقرير', 'error')
        return redirect(url_for('reports.bookings_report'))



@reports_bp.route('/rooms')
@login_required
@permission_required('view_reports')
def rooms_report():
    """تقرير الغرف"""
    try:
        rooms = Room.query.order_by(Room.room_number).all()
        
        # إحصائيات الغرف
        total_rooms = len(rooms)
        available_rooms = len([r for r in rooms if r.status == 'available'])
        occupied_rooms = len([r for r in rooms if r.status == 'occupied'])
        maintenance_rooms = len([r for r in rooms if r.status == 'maintenance'])
        
        stats = {
            'total_rooms': total_rooms,
            'available_rooms': available_rooms,
            'occupied_rooms': occupied_rooms,
            'maintenance_rooms': maintenance_rooms,
            'occupancy_rate': round((occupied_rooms / total_rooms) * 100, 1) if total_rooms > 0 else 0,
            'room_types': []
        }
    except:
        rooms = []
        stats = {
            'total_rooms': 0,
            'available_rooms': 0,
            'occupied_rooms': 0,
            'maintenance_rooms': 0,
            'occupancy_rate': 0,
            'room_types': []
        }
    
    return render_template('reports/rooms.html', 
                         title='تقرير الغرف', 
                         rooms=rooms, 
                         stats=stats)

@reports_bp.route('/customers')
@login_required
@permission_required('view_reports')
def customers_report():
    """تقرير العملاء"""
    try:
        customers = Customer.query.order_by(Customer.created_at.desc()).all()
        
        stats = {
            'total_customers': len(customers),
            'top_customers': []
        }
    except:
        customers = []
        stats = {'total_customers': 0, 'top_customers': []}
    
    return render_template('reports/customers.html', 
                         title='تقرير العملاء', 
                         customers=customers, 
                         stats=stats)

@reports_bp.route('/users')
@login_required
@permission_required('manage_users')
def users_report():
    """تقرير المستخدمين"""
    try:
        users = User.query.order_by(User.created_at.desc()).all()
        
        # إحصائيات المستخدمين
        user_stats = []
        for user in users:
            # For simplicity, just list permissions for now
            permissions_list = ', '.join([p.name for p in user.permissions])
            user_stats.append({'username': user.username, 'full_name': user.full_name, 'permissions': permissions_list})
        
        stats = {
            'total_users': len(users),
            'user_stats': user_stats
        }
    except Exception as e:
        print(f"Error in users_report: {e}")
        users = []
        stats = {'total_users': 0, 'user_stats': []}
    
    return render_template('reports/users.html',
                         title='تقرير المستخدمين',
                         users=users,
                         stats=stats)

@reports_bp.route('/comprehensive')
@login_required
@permission_required('view_reports')
def comprehensive_report():
    """التقرير الشامل مع الفلترة"""
    # الحصول على المعاملات من الطلب
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status')
    nationality = request.args.get('nationality')
    room_type = request.args.get('room_type')
    export_format = request.args.get('export', 'html')

    # بناء الاستعلام - استبعاد الحجوزات الملغية من التقارير
    query = Booking.query.join(Customer).join(Room).filter(Booking.status != 'cancelled')

    # دالة مساعدة لتحليل تواريخ متعددة التنسيقات مع دعم الأرقام العربية
    def _parse_date_flexible(value):
        if not value:
            return None
        try:
            s = str(value).strip()
            # تحويل الأرقام العربية/الفارسية إلى إنجليزية وإزالة المسافات الداخلية
            trans_map = str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹', '01234567890123456789')
            s = s.translate(trans_map).replace(' ', '')
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%d.%m.%Y'):
                try:
                    return datetime.strptime(s, fmt).date()
                except ValueError:
                    continue
            return None
        except Exception:
            return None

    # تطبيق الفلاتر
    start_date_obj = _parse_date_flexible(start_date)
    end_date_obj = _parse_date_flexible(end_date)

    # استخدام تواريخ الحجز المجدولة (الوصول/المغادرة) في الفلترة وفقًا لمتطلبات التقرير
    actual_check_in = Booking.check_in_date
    actual_check_out = Booking.check_out_date

    # منطق جديد: إظهار أي حجز تم تسجيل دخوله داخل الفترة المحددة فقط
    if start_date_obj and end_date_obj:
        query = query.filter(
            and_(
                actual_check_in >= start_date_obj,
                actual_check_in <= end_date_obj
            )
        )
    elif start_date_obj:
        # في حالة تحديد بداية فقط: أي حجز تم تسجيل دخوله بعد أو عند البداية
        query = query.filter(actual_check_in >= start_date_obj)
    elif end_date_obj:
        # في حالة تحديد نهاية فقط: أي حجز تم تسجيل دخوله قبل أو عند النهاية
        query = query.filter(actual_check_in <= end_date_obj)

    # شرط الحالة:
    # - إذا طلب المستخدم حالة محددة نطبقها كما هي (مع استمرار استبعاد الملغاة)
    # - وإلا: نعرض أي حجز تم تسجيل دخوله فعليًا (check_in_time موجود) أو حالته Checked-in/Checked-out
    allowed_statuses = ['pending', 'confirmed', 'checked_in', 'checked_out', 'cancelled']
    if status and status in allowed_statuses:
        if status != 'all':
            query = query.filter(Booking.status == status)
    else:
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Booking.status.in_(['checked_in', 'checked_out']),
                Booking.check_in_time.isnot(None)
            )
        )

    if nationality and nationality != 'all':
        query = query.filter(Customer.nationality == nationality)

    if room_type and room_type != 'all':
        query = query.filter(Room.room_type == room_type)

    # ترتيب النتائج
    bookings = query.order_by(Booking.check_in_date.desc()).all()

    # حساب الإحصائيات
    total_bookings = len(bookings)
    total_nights = sum([(booking.check_out_date - booking.check_in_date).days
                       for booking in bookings if booking.check_in_date and booking.check_out_date])
    total_revenue = sum([booking.total_price or 0 for booking in bookings])

    # الحصول على قوائم للفلاتر
    all_nationalities = db.session.query(Customer.nationality).filter(
        Customer.nationality.isnot(None),
        Customer.nationality != ''
    ).distinct().all()
    nationalities = [n[0] for n in all_nationalities if n[0]]

    all_room_types = db.session.query(Room.room_type).distinct().all()
    room_types = [rt[0] for rt in all_room_types if rt[0]]

    stats = {
        'total_bookings': total_bookings,
        'total_nights': total_nights,
        'total_revenue': total_revenue,
        'average_stay': round(total_nights / total_bookings, 1) if total_bookings > 0 else 0,
        'average_revenue': round(total_revenue / total_bookings, 2) if total_bookings > 0 else 0
    }

    filters = {
        'start_date': start_date,
        'end_date': end_date,
        'status': status,
        'nationality': nationality,
        'room_type': room_type,
        'nationalities': nationalities,
        'room_types': room_types
    }

    # إذا كان المطلوب تصدير PDF
    if export_format == 'pdf':
        return generate_pdf_report(bookings, stats, filters)

    # إذا كان المطلوب تصدير JSON
    if export_format == 'json':
        return generate_json_report(bookings, stats, filters)

    return render_template('reports/comprehensive.html',
                         title='التقرير الشامل',
                         bookings=bookings,
                         stats=stats,
                         filters=filters)

def generate_pdf_report(bookings, stats, filters, report_type='comprehensive'):
    """إنشاء تقرير PDF باستخدام ReportLab - حل مستقر للنص العربي على Windows"""
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from io import BytesIO
        import os
        from datetime import datetime
        import arabic_reshaper
        from bidi.algorithm import get_display

        logger.info("بدء إنشاء تقرير PDF باستخدام ReportLab...")

        # تحديد مسار الخط العربي - استخدام خط Amiri Bold للوضوح
        font_regular_path = os.path.join(os.path.dirname(__file__), '..', '..', 'fonts', 'Amiri-1.000', 'Amiri-Regular.ttf')
        font_bold_path = os.path.join(os.path.dirname(__file__), '..', '..', 'fonts', 'Amiri-1.000', 'Amiri-Bold.ttf')
        
        # تسجيل الخطوط العربية
        arabic_font = 'ArabicFont'
        arabic_font_bold = 'ArabicFontBold'
        
        try:
            # محاولة تحميل الخط Bold أولاً
            if os.path.exists(font_bold_path) and os.path.getsize(font_bold_path) > 0:
                pdfmetrics.registerFont(TTFont(arabic_font_bold, font_bold_path))
                arabic_font = arabic_font_bold  # استخدام Bold كخط افتراضي
                logger.info(f"تم تحميل الخط العربي Bold بنجاح: {font_bold_path}")
            elif os.path.exists(font_regular_path) and os.path.getsize(font_regular_path) > 0:
                pdfmetrics.registerFont(TTFont(arabic_font, font_regular_path))
                logger.info(f"تم تحميل الخط العربي Regular بنجاح: {font_regular_path}")
            else:
                # البحث عن أي خط عربي صالح متاح
                fonts_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'fonts')
                found_font = False
                
                if os.path.exists(fonts_dir):
                    # البحث في مجلد Amiri أولاً (أولوية للـ Bold)
                    amiri_dir = os.path.join(fonts_dir, 'Amiri-1.000')
                    if os.path.exists(amiri_dir):
                        for font_file in ['Amiri-Bold.ttf', 'Amiri-Regular.ttf']:
                            test_path = os.path.join(amiri_dir, font_file)
                            if os.path.exists(test_path) and os.path.getsize(test_path) > 0:
                                pdfmetrics.registerFont(TTFont(arabic_font, test_path))
                                logger.info(f"تم تحميل خط بديل: {test_path}")
                                found_font = True
                                break
                    
                    # إذا لم نجد في Amiri، ابحث في المجلد الرئيسي
                    if not found_font:
                        for font_file in os.listdir(fonts_dir):
                            if font_file.endswith('.ttf'):
                                test_path = os.path.join(fonts_dir, font_file)
                                if os.path.getsize(test_path) > 0:
                                    pdfmetrics.registerFont(TTFont(arabic_font, test_path))
                                    logger.info(f"تم تحميل خط متاح: {test_path}")
                                    found_font = True
                                    break
                
                if not found_font:
                    arabic_font = 'Helvetica-Bold'  # استخدام خط افتراضي Bold
                    logger.warning("لم يتم العثور على خط عربي صالح، سيتم استخدام Helvetica-Bold")
                    
        except Exception as e:
            arabic_font = 'Helvetica-Bold'
            logger.warning(f"خطأ في تحميل الخط العربي: {e}، سيتم استخدام Helvetica-Bold")

        def format_arabic_text(text):
            """تنسيق النص العربي للعرض الصحيح في PDF - حل بسيط وفعال"""
            if not text or not isinstance(text, str):
                return text
            
            try:
                # تطبيق arabic_reshaper مع إعدادات أساسية
                reshaped_text = arabic_reshaper.reshape(text)
                # تطبيق get_display() بدون معاملات إضافية
                bidi_text = get_display(reshaped_text)
                
                # إرجاع النص كما هو بعد المعالجة - بدون عكس إضافي
                return bidi_text
            except Exception as e:
                logger.warning(f"خطأ في تنسيق النص العربي: {e}")
                return text

        # إنشاء buffer للـ PDF
        pdf_buffer = BytesIO()
        
        # إنشاء مستند PDF
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=landscape(A4),
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )

        # إنشاء قائمة العناصر
        elements = []

        # إنشاء أنماط النص - أحجام مُحسنة للاستغلال الأمثل للمساحة
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontName=arabic_font,
            fontSize=16,  # تصغير من 24 إلى 16
            alignment=2,  # محاذاة يمين
            spaceAfter=8,  # تصغير من 12 إلى 8
            textColor=colors.HexColor('#2c3e50')
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=arabic_font,
            fontSize=10,  # تصغير من 16 إلى 10
            alignment=2,  # محاذاة يمين
            spaceAfter=4,  # تصغير من 6 إلى 4
            textColor=colors.black
        )

        try:
            logo_path = os.path.join(os.path.dirname(__file__), '..', '..', 'WhatsApp Image 2025-09-06 at 05.49.04_a590a673.jpg')
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=1.4*inch, height=1.4*inch)
                logo.hAlign = 'RIGHT'
                elements.append(logo)
                elements.append(Spacer(1, 6))
        except Exception:
            pass

        # إضافة العنوان الرئيسي
        title_text = format_arabic_text("تقرير شامل - نظام إدارة فندق قارون")
        title = Paragraph(title_text, title_style)
        elements.append(title)
        elements.append(Spacer(1, 6))

        # إضافة معلومات التقرير
        report_info = format_arabic_text(f"تاريخ إنشاء التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        info_para = Paragraph(report_info, normal_style)
        elements.append(info_para)
        
        bookings_count = format_arabic_text(f"عدد الحجوزات: {len(bookings)}")
        count_para = Paragraph(bookings_count, normal_style)
        elements.append(count_para)
        elements.append(Spacer(1, 6))

        # إضافة جدول الإحصائيات
        if stats:
            # عنوان قسم الإحصائيات
            stats_title = format_arabic_text("الإحصائيات العامة")
            stats_heading = Paragraph(stats_title, title_style)
            elements.append(stats_heading)
            elements.append(Spacer(1, 6))
            
            # حساب إحصائيات الجنسيات - بناءً على الصفوف المعروضة فعليًا فقط (العملاء الأساسيين والمرافقين النشطين)
            nationalities_customers = {}

            # تحليل تواريخ الفلتر محليًا هنا لضمان تطابق المنطق مع جدول البيانات
            try:
                from datetime import datetime as _dt
                def _parse_date_flex(v):
                    if not v:
                        return None
                    s = str(v).strip()
                    trans_map = str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹', '01234567890123456789')
                    s = s.translate(trans_map).replace(' ', '')
                    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%d.%m.%Y'):
                        try:
                            return _dt.strptime(s, fmt).date()
                        except ValueError:
                            continue
                    return None
                filter_start = _parse_date_flex(filters.get('start_date') if filters else None)
                filter_end = _parse_date_flex(filters.get('end_date') if filters else None)
            except Exception:
                filter_start = None
                filter_end = None

            for booking in bookings:
                # استخدام التواريخ/الأوقات الفعلية عند التوفر
                start_candidate = booking.check_in_time.date() if getattr(booking, 'check_in_time', None) else booking.check_in_date
                end_candidate = booking.check_out_time.date() if getattr(booking, 'check_out_time', None) else booking.check_out_date

                # حساب التداخل مع نافذة الفلتر
                overlap_start = start_candidate
                overlap_end = end_candidate
                if filter_start and overlap_start and overlap_start < filter_start:
                    overlap_start = filter_start
                if filter_end:
                    if overlap_end is None or overlap_end > filter_end:
                        overlap_end = filter_end

                # تخطّي الحجوزات التي لا يوجد لها تداخل إيجابي
                if not overlap_start or not overlap_end or overlap_end <= overlap_start:
                    continue

                # العميل الأساسي
                if getattr(booking, 'customer', None) and booking.customer.nationality:
                    nat = booking.customer.nationality
                    cid = booking.customer.id
                    if nat not in nationalities_customers:
                        nationalities_customers[nat] = set()
                    nationalities_customers[nat].add(cid)

                # المرافقون النشطون
                try:
                    active_guests = [g for g in getattr(booking, 'guests', []) if getattr(g, 'is_active', False)]
                    for g in active_guests:
                        if getattr(g, 'customer', None) and g.customer.nationality:
                            nat = g.customer.nationality
                            cid = g.customer.id
                            if nat not in nationalities_customers:
                                nationalities_customers[nat] = set()
                            nationalities_customers[nat].add(cid)
                except Exception:
                    pass

            # تحويل إلى عدد العملاء الفريدين لكل جنسية بعد التصفية
            nationalities_count = {nat: len(customers_set) for nat, customers_set in nationalities_customers.items()}
            
            # بيانات جدول الإحصائيات
            stats_data = [
                [format_arabic_text("البيان"), format_arabic_text("القيمة")]
            ]
            
            stats_data.append([
                format_arabic_text("عدد الجنسيات"), 
                str(len(nationalities_count))
            ])
            
            # إضافة كل جنسية في صف منفصل
            if nationalities_count:
                sorted_nationalities = sorted(nationalities_count.items(), key=lambda x: x[1], reverse=True)
                for item in sorted_nationalities:
                    if len(item) == 2:
                        nat, count = item
                        stats_data.append([
                            format_arabic_text(nat), 
                            str(count)
                        ])
            
            # إنشاء جدول الإحصائيات - مُحسن للاستغلال الأمثل للمساحة
            safe_stats_data = [row for row in stats_data if len(row) == 2]
            stats_table = Table(safe_stats_data, colWidths=[5.5*inch, 2.5*inch], rowHeights=None)
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f2f2f2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, -1), arabic_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),  # تصغير من 14 إلى 9
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  # تصغير من 15 إلى 6
                ('TOPPADDING', (0, 0), (-1, -1), 6),  # تصغير من 15 إلى 6
                ('LEFTPADDING', (0, 0), (-1, -1), 8),  # تصغير من 15 إلى 8
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),  # تصغير من 15 إلى 8
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),  # تصغير سُمك الحدود من 2 إلى 1
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))
            
            elements.append(stats_table)
            elements.append(Spacer(1, 6))

        # إضافة جدول الحجوزات
        if bookings:
            # عنوان قسم الحجوزات
            bookings_title = format_arabic_text("تفاصيل الحجوزات")
            bookings_heading = Paragraph(bookings_title, title_style)
            elements.append(bookings_heading)
            elements.append(Spacer(1, 6))
            
            # بيانات جدول الحجوزات
            bookings_data = [
                [
                    format_arabic_text("اسم العميل"),
                    format_arabic_text("رقم الهوية"),
                    format_arabic_text("الجنسية"),
                    format_arabic_text("العنوان"),
                    format_arabic_text("تاريخ الوصول"),
                    format_arabic_text("تاريخ المغادرة"),
                    format_arabic_text("عدد الأيام")
                ]
            ]
            
            # إضافة بيانات جميع الحجوزات (بدون حد) مع عرض المرافقين كصفوف مماثلة
            # استخدام فترة الفلتر لحساب فترة التقاطع فقط في العرض (تواريخ وعدد الأيام)
            try:
                from datetime import datetime as _dt
                def _parse_date_flex(v):
                    if not v:
                        return None
                    s = str(v).strip()
                    trans_map = str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹', '01234567890123456789')
                    s = s.translate(trans_map).replace(' ', '')
                    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%d.%m.%Y'):
                        try:
                            return _dt.strptime(s, fmt).date()
                        except ValueError:
                            continue
                    return None
                filter_start = _parse_date_flex(filters.get('start_date') if filters else None)
                filter_end = _parse_date_flex(filters.get('end_date') if filters else None)
            except Exception:
                filter_start = None
                filter_end = None

            for booking in bookings:
                # عرض تقاطع فترة الحجز المجدولة مع فترة الفلترة فقط (بدون استخدام الأوقات)
                start_candidate = booking.check_in_date
                end_candidate = booking.check_out_date

                if not start_candidate:
                    continue
                from datetime import timedelta

                # حساب التقاطع مع نافذة الفلترة (start_date/end_date)
                overlap_start = start_candidate
                overlap_end = end_candidate

                if filter_start and overlap_start and overlap_start < filter_start:
                    overlap_start = filter_start
                if filter_end:
                    if overlap_end is None or overlap_end > filter_end:
                        overlap_end = filter_end

                # تخطّي إذا لم يوجد تداخل إيجابي
                if not overlap_end or overlap_end <= overlap_start:
                    continue

                # حساب الأيام داخل نافذة التقاطع (ليالٍ)
                days_delta = (overlap_end - overlap_start).days
                days_count = 1 if days_delta <= 0 else days_delta

                # تحديد تواريخ العرض داخل النافذة فقط
                display_start = overlap_start
                display_end = overlap_end if days_delta > 0 else overlap_start + timedelta(days=1)

                check_in = display_start.strftime('%Y-%m-%d')
                check_out = display_end.strftime('%Y-%m-%d')

                # صف العميل الأساسي
                customer_name = format_arabic_text(booking.customer.name if booking.customer else 'غير محدد')
                customer_id = booking.customer.id_number if booking.customer and booking.customer.id_number else format_arabic_text('غير محدد')
                customer_nationality = format_arabic_text(booking.customer.nationality if booking.customer else 'غير محدد')
                customer_address = format_arabic_text(booking.customer.address if booking.customer and booking.customer.address else 'غير محدد')

                bookings_data.append([
                    customer_name,
                    customer_id,
                    customer_nationality,
                    customer_address,
                    check_in,
                    check_out,
                    str(days_count)
                ])

                # صفوف المرافقين ضمن نفس فترة التقاطع
                try:
                    _active_or_present_guests = []
                    for g in getattr(booking, 'guests', []):
                        present = getattr(g, 'is_active', False) is True
                        if not present:
                            rt = getattr(g, 'removed_time', None)
                            try:
                                if rt is None or (hasattr(rt, 'date') and rt.date() >= overlap_start):
                                    present = True
                            except Exception:
                                pass
                        if present:
                            _active_or_present_guests.append(g)

                    for g in _active_or_present_guests:
                        g_name = format_arabic_text(g.customer.name if g.customer else 'غير محدد')
                        g_id = g.customer.id_number if g.customer and g.customer.id_number else format_arabic_text('غير محدد')
                        g_nat = format_arabic_text(g.customer.nationality if g.customer and g.customer.nationality else 'غير محدد')
                        g_addr = format_arabic_text(g.customer.address if g.customer and g.customer.address else 'غير محدد')

                        bookings_data.append([
                            g_name,
                            g_id,
                            g_nat,
                            g_addr,
                            check_in,
                            check_out,
                            str(days_count)
                        ])
                except Exception as _e:
                    logger.warning(f'تعذر إضافة صفوف المرافقين للحجز {getattr(booking, "id", "?")}: {_e}')
            
            # إنشاء جدول الحجوزات - مُحسن للاستغلال الأمثل للمساحة
            # ضبط أعرض الأعمدة بعد إضافة "العنوان"
            bookings_table = Table(bookings_data, colWidths=[2.0*inch, 1.4*inch, 1.3*inch, 2.4*inch, 1.2*inch, 1.2*inch, 0.9*inch], rowHeights=None)  # أعمدة أصغر
            bookings_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f4fd')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, -1), arabic_font),
                ('FONTSIZE', (0, 0), (-1, -1), 8),  # تصغير من 12 إلى 8
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),  # تصغير من 15 إلى 4
                ('TOPPADDING', (0, 0), (-1, -1), 4),  # تصغير من 15 إلى 4
                ('LEFTPADDING', (0, 0), (-1, -1), 6),  # تصغير من 12 إلى 6
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),  # تصغير من 12 إلى 6
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),  # تصغير سُمك الحدود من 2 إلى 1
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                # تمت إزالة ROWBACKGROUNDS و LEADING لضمان التوافق مع بعض إصدارات ReportLab
            ]))
            
            elements.append(bookings_table)

            # تمت إزالة قسم "تفاصيل المرافقين" لأن المرافقين أصبحوا يظهرون كصفوف مماثلة للعملاء ضمن نفس الجدول

        # بناء المستند
        doc.build(elements)
        pdf_buffer.seek(0)
        
        logger.info("تم إنشاء تقرير PDF بنجاح باستخدام ReportLab")
        
        # إنشاء الاستجابة
        pdf_data = pdf_buffer.getvalue()
        pdf_buffer.close()
        
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        # عرض داخل المتصفح بدل التنزيل
        response.headers['Content-Disposition'] = f'inline; filename=comprehensive_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        # تحسين التوافق مع العروض داخل المتصفح
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        return response

    except ImportError as e:
        error_message = f'مكتبة ReportLab غير مثبتة. يرجى تثبيتها باستخدام: pip install reportlab. الخطأ: {e}'
        logger.error(error_message)
        flash(error_message, 'danger')
        return redirect(url_for('reports.comprehensive_report'))
    except Exception as e:
        # تسجيل الخطأ الفعلي للمساعدة في التشخيص
        logger.error(f"حدث خطأ غير متوقع عند إنشاء PDF: {e}")
        logger.error(traceback.format_exc())
        
        error_message = f'حدث خطأ فني أثناء إنشاء تقرير PDF. يرجى مراجعة سجلات الخادم. الخطأ: {e}'
        flash(error_message, 'danger')
        return redirect(url_for('reports.comprehensive_report'))

def generate_json_report(bookings, stats, filters):
    """إنشاء تقرير JSON"""
    data = {
        'report_info': {
            'generated_at': datetime.now().isoformat(),
            'filters': filters,
            'stats': stats
        },
        'bookings': []
    }

    for booking in bookings:
        booking_data = {
            'id': booking.id,
            'customer_name': booking.customer.name,
            'customer_nationality': booking.customer.nationality,
            'customer_id_number': booking.customer.id_number,
            'customer_phone': booking.customer.phone,
            'room_number': booking.room.room_number,
            'room_type': booking.room.room_type,
            'check_in_date': booking.check_in_date.isoformat() if booking.check_in_date else None,
            'check_out_date': booking.check_out_date.isoformat() if booking.check_out_date else None,
            'nights': (booking.check_out_date - booking.check_in_date).days if booking.check_in_date and booking.check_out_date else 0,
            'status': booking.status,
            'total_price': float(booking.total_price or 0),
            'occupancy_type': booking.occupancy_type,
            'is_deus': booking.is_deus
        }
        data['bookings'].append(booking_data)

    response = make_response(json.dumps(data, ensure_ascii=False, indent=2))
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=comprehensive_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

    return response
