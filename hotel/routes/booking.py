from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from sqlalchemy import and_, or_
from wtforms.validators import DataRequired, ValidationError

from hotel import db
from hotel.models import Booking, Room, Customer, Payment
from hotel.forms.booking import BookingForm, BookingSearchForm
from hotel.utils.decorators import permission_required
from hotel.utils.activity_logger import log_activity

def check_room_availability_for_booking(room_id, check_in_date, check_out_date, exclude_booking_id=None):
    """
    التحقق من توفر الغرفة للحجز في فترة معينة

    Args:
        room_id: معرف الغرفة
        check_in_date: تاريخ الوصول
        check_out_date: تاريخ المغادرة
        exclude_booking_id: معرف الحجز المستثنى (للتعديل)

    Returns:
        tuple: (is_available, conflicting_booking)
    """
    query = Booking.query.filter(
        Booking.room_id == room_id,
        Booking.status.in_(['confirmed', 'checked_in']),
        or_(
            and_(Booking.check_in_date <= check_in_date, Booking.check_out_date > check_in_date),
            and_(Booking.check_in_date < check_out_date, Booking.check_out_date >= check_out_date),
            and_(Booking.check_in_date >= check_in_date, Booking.check_out_date <= check_out_date)
        )
    )

    # استثناء حجز معين (مفيد عند التعديل)
    if exclude_booking_id:
        query = query.filter(Booking.id != exclude_booking_id)

    conflicting_booking = query.first()
    return conflicting_booking is None, conflicting_booking


def update_room_status(room_id):
    """تحديث حالة الغرفة بناءً على الحجوزات النشطة"""
    room = Room.query.get(room_id)
    if not room:
        return

    today = date.today()

    # تطبيق منطق التحرر الساعة 1 ظهرًا بتوقيت مصر
    from hotel.utils.datetime_utils import get_egypt_now
    now = get_egypt_now()
    cutoff_passed = now.hour >= 13

    # التحقق من وجود حجز نشط لهذه الغرفة اليوم وفقًا للحد الزمني
    base_filters = [
        Booking.room_id == room.id,
        Booking.check_in_date <= today,
        Booking.status.in_(['confirmed', 'checked_in'])
    ]
    if cutoff_passed:
        # بعد 1 ظهرًا: يوم المغادرة لا يحجز الغرفة
        base_filters.append(Booking.check_out_date > today)
    else:
        # قبل 1 ظهرًا: يوم المغادرة يعتبر مشغول
        base_filters.append(Booking.check_out_date >= today)

    active_booking = Booking.query.filter(*base_filters).first()

    # تحديث حالة الغرفة (إلا إذا كانت في صيانة)
    if room.status != 'maintenance':
        if active_booking:
            room.status = 'occupied'
        else:
            room.status = 'available'

    db.session.commit()

booking_bp = Blueprint('booking', __name__, url_prefix='/bookings')

@booking_bp.route('/')
@login_required
def index():
    # التحقق من الصلاحية
    if not current_user.has_permission('manage_bookings'):
        flash('ليس لديك صلاحية لعرض جميع الحجوزات', 'danger')
        if current_user.has_permission('admin'):
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('user.dashboard'))

    # استعلام بسيط مع ترقيم الصفحات
    page = request.args.get('page', 1, type=int)
    per_page = 15  # عدد الحجوزات في كل صفحة

    # جلب جميع الحجوزات مرتبة حسب التاريخ
    bookings = Booking.query.order_by(Booking.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('booking/index.html', title='جميع الحجوزات', bookings=bookings)

@booking_bp.route('/my-bookings')
@login_required
def my_bookings():
    """إعادة توجيه إلى لوحة التحكم المناسبة"""
    if current_user.has_permission('admin'):
        return redirect(url_for('admin.dashboard'))
    else:
        return redirect(url_for('user.dashboard'))

@booking_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    # التحقق من الصلاحية
    if not current_user.can_create_booking():
        flash('ليس لديك صلاحية لإنشاء حجز جديد', 'danger')
        return redirect(url_for('main.index'))
    """إنشاء حجز جديد - مع البحث اليدوي للعملاء"""
    form = BookingForm()

    # إعداد خيارات الغرف - جلب جميع الغرف
    rooms = Room.query.all()
    if not rooms:
        # إنشاء غرف تجريبية إذا لم تكن موجودة
        test_rooms = [
            Room(room_number='101', room_type='standard', price_per_night=800, capacity=2, status='available'),
            Room(room_number='102', room_type='deluxe', price_per_night=1200, capacity=3, status='available'),
            Room(room_number='103', room_type='suite', price_per_night=1800, capacity=4, status='available'),
        ]
        for room in test_rooms:
            db.session.add(room)
        db.session.commit()
        rooms = Room.query.all()

    # إعداد خيارات النموذج
    room_choices = [('', 'اختر الغرفة...')]
    for r in rooms:
        room_type_display = r.get_room_type_display() if hasattr(r, 'get_room_type_display') else r.room_type
        price_display = f' - {r.price_per_night} جنيه/ليلة' if hasattr(r, 'price_per_night') else ''
        room_choices.append((r.id, f'غرفة {r.room_number} - {room_type_display}{price_display}'))

    form.room_id.choices = room_choices

    # تعبئة افتراضية من باراميترات الرابط (عند فتح الصفحة من التقويم)
    if request.method == 'GET':
        try:
            pre_room_id = request.args.get('room_id')
            if pre_room_id:
                pre_room_id_int = int(pre_room_id)
                if any(choice[0] == pre_room_id_int for choice in room_choices if choice[0] != ''):
                    form.room_id.data = pre_room_id_int
            pre_check_in = request.args.get('check_in')
            pre_check_out = request.args.get('check_out')
            if pre_check_in:
                form.check_in_date.data = datetime.strptime(pre_check_in, '%Y-%m-%d').date()
            if pre_check_out:
                form.check_out_date.data = datetime.strptime(pre_check_out, '%Y-%m-%d').date()
        except Exception:
            pass

    # التأكد من وجود عملاء تجريبيين
    customers = Customer.query.all()
    if not customers:
        test_customers = [
            Customer(name='أحمد محمد علي', id_number='12345678901234', phone='01012345678', email='ahmed@example.com'),
            Customer(name='فاطمة أحمد حسن', id_number='98765432109876', phone='01098765432', email='fatma@example.com'),
            Customer(name='محمد عبد الله', id_number='11111111111111', phone='01111111111', email='mohamed@example.com'),
        ]
        for customer in test_customers:
            db.session.add(customer)
        db.session.commit()

    if form.validate_on_submit():
        try:
            # التحقق من حالة العميل المحدد
            customer_id = form.customer_id.data
            if customer_id:
                customer = Customer.query.get(customer_id)
                if customer and customer.is_blocked:
                    flash(f'لا يمكن إنشاء حجز للعميل {customer.name} - العميل محظور: {customer.block_reason}', 'danger')
                    return render_template('booking/create.html', form=form, title='إنشاء حجز جديد')
            
            # التحقق من البيانات
            customer = Customer.query.get(form.customer_id.data)
            room = Room.query.get(form.room_id.data)

            if not customer:
                flash('العميل المحدد غير موجود', 'error')
                return render_template('booking/create.html', title='حجز جديد', form=form, rooms=rooms)

            if not room:
                flash('الغرفة المحددة غير موجودة', 'error')
                return render_template('booking/create.html', title='حجز جديد', form=form, rooms=rooms)

            # التحقق من توفر الغرفة أولاً
            is_available, conflicting_booking = check_room_availability_for_booking(
                room.id, form.check_in_date.data, form.check_out_date.data
            )

            if not is_available:
                flash(f'عذراً، الغرفة رقم {room.room_number} محجوزة بالفعل من {conflicting_booking.check_in_date} إلى {conflicting_booking.check_out_date} للعميل {conflicting_booking.customer.name}', 'error')
                return render_template('booking/create.html', title='حجز جديد', form=form, rooms=rooms)

            # حساب السعر
            days = (form.check_out_date.data - form.check_in_date.data).days
            if days <= 0:
                flash('تاريخ المغادرة يجب أن يكون بعد تاريخ الوصول', 'error')
                return render_template('booking/create.html', title='حجز جديد', form=form, rooms=rooms)

            # أسعار الديوز والعادي
            if form.is_deus.data:
                prices = {'single': 600, 'double': 800, 'triple': 1000}
            else:
                # تطبيق الأسعار الجديدة بداية من 2026
                if form.check_in_date.data.year >= 2026:
                    prices = {'single': 900, 'double': 1250, 'triple': 1500}
                else:
                    prices = {'single': 800, 'double': 1100, 'triple': 1400}

            default_price = 900 if (not form.is_deus.data and form.check_in_date.data.year >= 2026) else 800
            price_per_night = prices.get(form.occupancy_type.data, default_price)
            base_price = price_per_night * days

            # حساب الضريبة أولاً على المبلغ الأساسي
            tax_percentage = 14.0 if form.include_tax.data else 0.0
            tax_amount = (base_price * tax_percentage) / 100 if form.include_tax.data else 0.0
            total_with_tax = base_price + tax_amount

            # تطبيق الخصم على الإجمالي (شامل الضريبة)
            discount_percentage = form.discount_percentage.data or 0
            discount_amount = (total_with_tax * discount_percentage) / 100
            total_price = total_with_tax - discount_amount
            after_discount = total_price - tax_amount  # للعرض فقط

            # إنشاء الحجز
            booking = Booking(
                customer_id=customer.id,
                room_id=room.id,
                user_id=current_user.id,
                check_in_date=form.check_in_date.data,
                check_out_date=form.check_out_date.data,
                occupancy_type=form.occupancy_type.data,
                is_deus=form.is_deus.data,
                base_price=base_price,
                discount_percentage=discount_percentage,
                tax_percentage=tax_percentage,
                tax_amount=tax_amount,
                total_price=total_price,
                notes=form.notes.data
            )

            # تحديد سنة الحجز وترقيمه السنوي بناءً على تاريخ إنشاء الحجز (بتوقيت مصر)
            from hotel.utils.datetime_utils import get_egypt_now
            booking_year = get_egypt_now().year
            booking.booking_year = booking_year
            booking.year_seq = Booking.next_sequence_for_year(booking_year)

            # تعيين الحالة
            booking.status = 'confirmed'

            db.session.add(booking)
            db.session.commit()

            # تحديث حالة الغرفة
            update_room_status(room.id)

            # تسجيل النشاط
            log_activity(current_user, 'create_booking', f'Created booking #{booking.booking_code} for customer {customer.name}')

            flash(f'تم إنشاء الحجز بنجاح - رقم الحجز: {booking.booking_code}', 'success')
            # إعادة توجيه لصفحة حجز جديد لبدء حجز آخر
            return redirect(url_for('booking.create'))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إنشاء الحجز: {str(e)}', 'error')

    return render_template('booking/create.html', title='حجز جديد', form=form, rooms=rooms)


@booking_bp.route('/new-search-customers')
def new_search_customers():
    """البحث الجديد عن العملاء"""
    query = request.args.get('q', '').strip()

    # جلب جميع العملاء
    customers = Customer.query.all()

    # فلترة حسب البحث
    if query:
        filtered = []
        for customer in customers:
            if (customer.name and query.lower() in customer.name.lower()) or \
               (customer.id_number and query in customer.id_number) or \
               (customer.phone and query in customer.phone):
                filtered.append(customer)
        customers = filtered

    # تحويل إلى JSON
    results = []
    for customer in customers:
        results.append({
            'id': customer.id,
            'name': customer.name,
            'id_number': customer.id_number,
            'phone': customer.phone or ''
        })

    return jsonify({'success': True, 'customers': results})


@booking_bp.route('/all-customers')
@login_required
def all_customers():
    """عرض جميع العملاء للاختبار"""
    customers = Customer.query.all()
    results = []
    for customer in customers:
        results.append({
            'id': customer.id,
            'name': customer.name,
            'id_number': customer.id_number,
            'phone': customer.phone or ''
        })
    return jsonify({'total': len(customers), 'customers': results})


@booking_bp.route('/test-customers')
@login_required
def test_customers():
    """اختبار وجود العملاء"""
    customers = Customer.query.all()
    return jsonify({
        'total': len(customers),
        'customers': [{'id': c.id, 'name': c.name, 'id_number': c.id_number} for c in customers[:5]]
    })


@booking_bp.route('/debug-customers')
@login_required
def debug_customers():
    """عرض جميع العملاء للتشخيص"""
    try:
        customers = Customer.query.all()
        results = []
        for customer in customers:
            results.append({
                'id': customer.id,
                'name': customer.name,
                'id_number': customer.id_number,
                'phone': customer.phone or '',
                'nationality': customer.nationality or '',
                'address': customer.address or ''
            })
        return jsonify({
            'total_customers': len(customers),
            'customers': results
        })
    except Exception as e:
        return jsonify({'error': str(e)})


@booking_bp.route('/available-rooms')
def available_rooms():
    """جلب الغرف المتاحة في التواريخ المحددة"""
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')

    try:
        # جلب جميع الغرف أولاً للاختبار
        all_rooms = Room.query.all()
        print(f"DEBUG: إجمالي الغرف في قاعدة البيانات: {len(all_rooms)}")

        if not check_in or not check_out:
            # إرجاع جميع الغرف إذا لم تكن التواريخ محددة
            available_rooms = []
            for room in all_rooms:
                available_rooms.append({
                    'id': room.id,
                    'room_number': room.room_number,
                    'room_type': room.get_room_type_display() if hasattr(room, 'get_room_type_display') else room.room_type,
                    'price_per_night': float(room.price_per_night),
                    'capacity': room.capacity,
                    'description': room.description or ''
                })

            return jsonify({
                'success': True,
                'rooms': available_rooms,
                'total': len(available_rooms),
                'message': 'جميع الغرف (بدون فلترة التواريخ)'
            })

        # تحويل التواريخ
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()

        if check_in_date >= check_out_date:
            return jsonify({'success': False, 'message': 'تاريخ المغادرة يجب أن يكون بعد تاريخ الوصول'})

        available_rooms = []

        for room in all_rooms:
            # فحص الحجوزات المتداخلة
            overlapping_bookings = Booking.query.filter(
                Booking.room_id == room.id,
                Booking.status.in_(['pending', 'confirmed', 'checked_in']),
                or_(
                    and_(Booking.check_in_date <= check_in_date, Booking.check_out_date > check_in_date),
                    and_(Booking.check_in_date < check_out_date, Booking.check_out_date >= check_out_date),
                    and_(Booking.check_in_date >= check_in_date, Booking.check_out_date <= check_out_date)
                )
            ).count()

            if overlapping_bookings == 0:
                available_rooms.append({
                    'id': room.id,
                    'room_number': room.room_number,
                    'room_type': room.get_room_type_display() if hasattr(room, 'get_room_type_display') else room.room_type,
                    'price_per_night': float(room.price_per_night),
                    'capacity': room.capacity,
                    'description': room.description or ''
                })

        return jsonify({
            'success': True,
            'rooms': available_rooms,
            'total': len(available_rooms)
        })

    except Exception as e:
        print(f"DEBUG: خطأ في available_rooms: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'خطأ: {str(e)}'})


@booking_bp.route('/check-room-availability')
@login_required
def check_room_availability():
    """التحقق من توفر الغرفة في التواريخ المحددة"""
    room_number = request.args.get('room_number')
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    occupancy_type = request.args.get('occupancy_type', 'single')
    
    if not all([room_number, check_in, check_out]):
        return jsonify({'available': False, 'message': 'بيانات ناقصة'})
    
    try:
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
        
        # البحث عن الغرفة
        room = Room.query.filter_by(room_number=room_number).first()
        if not room:
            return jsonify({'available': False, 'message': 'الغرفة غير موجودة'})
        
        # التحقق من توفر الغرفة
        is_available, conflicting_booking = check_room_availability_for_booking(
            room.id, check_in_date, check_out_date
        )

        if not is_available:
            return jsonify({
                'available': False,
                'message': f'الغرفة محجوزة من {conflicting_booking.check_in_date} إلى {conflicting_booking.check_out_date}'
            })
        
        # حساب السعر
        days = (check_out_date - check_in_date).days
        
        # تطبيق الأسعار الجديدة بداية من 2026
        if check_in_date.year >= 2026:
            prices = {'single': 900, 'double': 1250, 'triple': 1500}
        else:
            prices = {'single': 800, 'double': 1100, 'triple': 1400}
            
        price_per_night = prices.get(occupancy_type, prices['single'])
        total_price = price_per_night * days
        
        return jsonify({
            'available': True,
            'price_per_night': price_per_night,
            'total_price': total_price,
            'occupancy_type': occupancy_type,
            'message': f'الغرفة {room_number} متاحة للحجز'
        })
        
    except Exception as e:
        return jsonify({'available': False, 'message': f'خطأ: {str(e)}'})
@booking_bp.route('/<int:id>')
@login_required
def details(id):
    from datetime import datetime
    
    booking = Booking.query.get_or_404(id)

    # Check if user has permission to view this booking
    if not current_user.has_permission('manage_bookings') and booking.user_id != current_user.id:
        flash('ليس لديك صلاحية لعرض هذا الحجز', 'danger')
        if current_user.has_permission('admin'):
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('user.dashboard'))

    # تمرير الوقت الحالي للقالب لعرضه في نافذة التأكيد
    now = datetime.now()

    return render_template('booking/details.html', 
                         title=f'تفاصيل الحجز #{booking.id}', 
                         booking=booking,
                         now=now)

@booking_bp.route('/<int:id>/pdf')
@login_required
def booking_pdf(id):
    """توليد PDF منسق لتفاصيل الحجز مع دعم العربية وخط واضح"""
    from io import BytesIO
    from datetime import datetime
    from flask import make_response

    # جلب الحجز والتحقق من الصلاحيات
    booking = Booking.query.get_or_404(id)
    if not current_user.has_permission('manage_bookings') and booking.user_id != current_user.id:
        flash('ليس لديك صلاحية لطباعة هذا الحجز', 'danger')
        return redirect(url_for('booking.details', id=id))

    try:
        # استيراد أدوات ReportLab
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import os
        import arabic_reshaper
        from bidi.algorithm import get_display

        # تهيئة الخط العربي (تسجيل العادي والعريض)
        fonts_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'fonts', 'Amiri-1.000')
        font_regular_path = os.path.join(fonts_dir, 'Amiri-Regular.ttf')
        font_bold_path = os.path.join(fonts_dir, 'Amiri-Bold.ttf')
        arabic_font_regular = 'ArabicFont'
        arabic_font_bold = 'ArabicFontBold'
        try:
            if os.path.exists(font_regular_path) and os.path.getsize(font_regular_path) > 0:
                pdfmetrics.registerFont(TTFont(arabic_font_regular, font_regular_path))
            if os.path.exists(font_bold_path) and os.path.getsize(font_bold_path) > 0:
                pdfmetrics.registerFont(TTFont(arabic_font_bold, font_bold_path))
            # fallback إن لم تتوفر الخطوط
            if not (os.path.exists(font_regular_path) or os.path.exists(font_bold_path)):
                arabic_font_regular = arabic_font_bold = 'Helvetica-Bold'
        except Exception:
            arabic_font_regular = arabic_font_bold = 'Helvetica-Bold'

        def ar(text: str) -> str:
            if text is None:
                return ''
            try:
                return get_display(arabic_reshaper.reshape(str(text)))
            except Exception:
                return str(text)

        # حساب البيانات المطلوبة
        customer_name = booking.customer.full_name if getattr(booking, 'customer', None) else '-'
        customer_phone = booking.customer.phone if getattr(booking, 'customer', None) else '-'
        room_number = booking.room.room_number if getattr(booking, 'room', None) else '-'
        
        def booking_number_only(code):
            if not code:
                return ""
            try:
                code_str = str(code)
                if '/' in code_str:
                    return code_str.split('/')[-1]
                return code_str
            except Exception:
                return str(code) if code else ""

        booking_code_full = booking.booking_code or booking.id
        booking_code = booking_number_only(booking_code_full)

        check_in = booking.check_in_date
        check_out = booking.check_out_date
        nights = (check_out - check_in).days if check_in and check_out else 0
        paid_amount = getattr(booking, 'paid_amount', 0) or 0
        remaining_amount = getattr(booking, 'remaining_amount', 0) or 0
        total_price = getattr(booking, 'total_price', 0) or 0
        printed_by = current_user.full_name or current_user.username
        printed_at = datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')
        # تحويل التنسيق إلى صيغة 12 ساعة مع "م" للعصر
        printed_at = printed_at.replace('AM', 'ص').replace('PM', 'م')

        # إنشاء المستند مع هوامش مريحة
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=48,
            bottomMargin=30
        )

        # أنماط متوازنة
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('TitleAR', parent=styles['Title'], fontName=arabic_font_bold, fontSize=21, leading=25, alignment=1, textColor=colors.HexColor('#2c3e50'))
        section_style = ParagraphStyle('SectionAR', parent=styles['Heading2'], fontName=arabic_font_bold, fontSize=13, leading=17, alignment=2, textColor=colors.HexColor('#34495e'), spaceAfter=6)
        label_style = ParagraphStyle('LabelAR', parent=styles['Normal'], fontName=arabic_font_bold, fontSize=11, leading=15, alignment=2)
        value_style = ParagraphStyle('ValueAR', parent=styles['Normal'], fontName=arabic_font_bold, fontSize=11, leading=15, alignment=2)
        small_style = ParagraphStyle('SmallAR', parent=styles['Normal'], fontName=arabic_font_bold, fontSize=10, leading=13, alignment=2, textColor=colors.HexColor('#8B4513'))

        elements = []

        # الشعار
        try:
            logo_path = os.path.join(os.path.dirname(__file__), '..', '..', 'WhatsApp Image 2025-09-06 at 05.49.04_a590a673.jpg')
            if os.path.exists(logo_path):
                from reportlab.platypus import Image as RLImage
                from reportlab.lib.utils import ImageReader
                img_reader = ImageReader(logo_path)
                iw, ih = img_reader.getSize()
                max_width = 90
                ratio = max_width / float(iw)
                logo = RLImage(logo_path, width=max_width, height=ih * ratio)
                logo.hAlign = 'RIGHT'
                elements.append(logo)
                elements.append(Spacer(1, 14))
        except Exception:
            pass

        # تجهيز طريقة الدفع
        payment_method_display = '-'
        try:
            last_payment = booking.payments.order_by(Payment.payment_date.desc()).first()
            if last_payment:
                type_map = {'cash': 'نقدي', 'card': 'بطاقة ائتمان', 'bank_transfer': 'تحويل بنكي'}
                payment_method_display = type_map.get(last_payment.payment_type, last_payment.payment_type or '-')
        except Exception:
            pass

        # جدول بيانات أساسية
        # تحسين أنماط التسميات والقيم
        label_style_clear = label_style.clone('label_style_clear')
        label_style_clear.alignment = 2  # يمين
        label_style_clear.letterSpacing = 0.1  # تحسين التباعد بين الحروف
        
        value_style_clear = value_style.clone('value_style_clear')
        value_style_clear.alignment = 2  # يمين
        value_style_clear.letterSpacing = 0.1  # تحسين التباعد بين الحروف
        
        details_rows = [
            [Paragraph(ar(booking_code), value_style_clear), Paragraph(ar('رقم الحجز'), label_style_clear)],
            [Paragraph(ar(customer_name), value_style_clear), Paragraph(ar('اسم العميل'), label_style_clear)],
            [Paragraph(ar(customer_phone or '-'), value_style_clear), Paragraph(ar('رقم الهاتف'), label_style_clear)],
        ]
        details_table = Table(details_rows, colWidths=[320, 140])
        details_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), arabic_font_bold),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ]))
        elements.append(details_table)
        elements.append(Spacer(1, 14))

        # --- التفاصيل المالية ---
        # استخدام نمط مخصص لتحسين وضوح النص العربي
        section_style_clear = section_style.clone('section_style_clear')
        section_style_clear.alignment = 1  # مركزية
        elements.append(Paragraph(ar('التفاصيل المالية'), section_style_clear))
        elements.append(Spacer(1, 7))

        base_price = getattr(booking, 'base_price', 0) or 0
        tax_amount = getattr(booking, 'tax_amount', 0) or 0
        total_before_discount = base_price + tax_amount
        discount_amount = (total_before_discount * (getattr(booking, 'discount_percentage', 0) or 0)) / 100

        # تحسين أنماط التسميات والقيم
        label_style_clear = label_style.clone('label_style_clear')
        label_style_clear.alignment = 2  # يمين
        label_style_clear.letterSpacing = 0.1  # تحسين التباعد بين الحروف
        
        value_style_clear = value_style.clone('value_style_clear')
        value_style_clear.alignment = 2  # يمين
        value_style_clear.letterSpacing = 0.1  # تحسين التباعد بين الحروف
        
        financial_details_data = [
            [Paragraph(ar(f'{base_price:.2f}'), value_style_clear), Paragraph(ar('سعر الإقامة الأساسي'), label_style_clear)],
            [Paragraph(ar(f'{tax_amount:.2f}'), value_style_clear), Paragraph(ar('ضريبة القيمة المضافة (14%)'), label_style_clear)],
            [Paragraph(ar(f'-{discount_amount:.2f}'), value_style_clear), Paragraph(ar(f'خصم ({booking.discount_percentage or 0}%)'), label_style_clear)],
            [Paragraph(ar(f'{total_price:.2f}'), label_style_clear), Paragraph(ar('الإجمالي النهائي'), label_style_clear)],
        ]
        financial_details_table = Table(financial_details_data, colWidths=[200, 260])
        financial_details_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), arabic_font_bold),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#eafaf1')),
        ]))
        elements.append(financial_details_table)
        elements.append(Spacer(1, 14))

        # --- ملخص الدفع ---
        # استخدام نمط مخصص لتحسين وضوح النص العربي
        section_style_clear = section_style.clone('section_style_clear')
        section_style_clear.alignment = 1  # مركزية
        elements.append(Paragraph(ar('ملخص الدفع'), section_style_clear))
        elements.append(Spacer(1, 7))
        
        # تحسين أنماط التسميات والقيم
        label_style_clear = label_style.clone('label_style_clear')
        label_style_clear.alignment = 2  # يمين
        label_style_clear.letterSpacing = 0.1  # تحسين التباعد بين الحروف
        
        value_style_clear = value_style.clone('value_style_clear')
        value_style_clear.alignment = 2  # يمين
        value_style_clear.letterSpacing = 0.1  # تحسين التباعد بين الحروف
        
        summary_data = [
            [Paragraph(ar(f'{paid_amount:.2f}'), value_style_clear), Paragraph(ar('إجمالي المدفوع'), label_style_clear)],
            [Paragraph(ar(f'{remaining_amount:.2f}'), value_style_clear), Paragraph(ar('المبلغ المتبقي'), label_style_clear)],
        ]
        summary_table = Table(summary_data, colWidths=[200, 260])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), arabic_font_bold),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#f0fff0'), colors.HexColor('#fff0f0')]),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 14))

        # --- سجل الدفعات ---
        payments = booking.payments.order_by(Payment.payment_date.asc()).all()
        if payments:
            # استخدام نمط مخصص لتحسين وضوح النص العربي
            section_style_clear = section_style.clone('section_style_clear')
            section_style_clear.alignment = 1  # مركزية
            elements.append(Paragraph(ar('سجل الدفعات'), section_style_clear))
            elements.append(Spacer(1, 7))

            type_map = {'cash': 'نقدي', 'card': 'بطاقة ائتمان', 'bank_transfer': 'تحويل بنكي'}

            # تحسين أنماط التسميات والقيم
            label_style_clear = label_style.clone('label_style_clear')
            label_style_clear.alignment = 2  # يمين
            label_style_clear.letterSpacing = 0.1  # تحسين التباعد بين الحروف
            
            value_style_clear = value_style.clone('value_style_clear')
            value_style_clear.alignment = 2  # يمين
            value_style_clear.letterSpacing = 0.1  # تحسين التباعد بين الحروف
            
            payment_history_data = [[
                Paragraph(ar('المبلغ'), label_style_clear),
                Paragraph(ar('تاريخ الدفعة'), label_style_clear),
                Paragraph(ar('طريقة الدفع'), label_style_clear),
                Paragraph(ar('ملاحظات'), label_style_clear),
            ]]
            for p in payments:
                payment_type_display = type_map.get(p.payment_type, p.payment_type or '-')
                payment_history_data.append([
                    Paragraph(ar(f'{p.amount:.2f}'), value_style_clear),
                    Paragraph(ar(p.payment_date.strftime('%Y-%m-%d')), value_style_clear),
                    Paragraph(ar(payment_type_display), value_style_clear),
                    Paragraph(ar(p.notes or '-'), value_style_clear),
                ])

            payment_history_table = Table(payment_history_data, colWidths=[80, 100, 100, 180])
            payment_history_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), arabic_font_bold),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eef2f7')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(payment_history_table)
            elements.append(Spacer(1, 14))
        elements.append(Spacer(1, 16))

        # مدة الإقامة
        stay_lines = []
        if check_in and check_out:
            stay_lines.append(Paragraph(ar(f'المدة: من {check_in} إلى {check_out}'), value_style))
        stay_lines.append(Paragraph(ar(f'عدد الليالي: {nights}'), value_style))
        for p in stay_lines:
            elements.append(p)
        elements.append(Spacer(1, 18))

        # معلومات الطباعة
        elements.append(Paragraph(ar(f'انشئ التقرير بواسطة: {printed_by}'), small_style))
        elements.append(Paragraph(ar(f'تاريخ الانشاء: {printed_at}'), small_style))
        # ملاحظة عن موعد الاستلام والتسليم
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(ar(f'ملاحظة: موعد استلام الغرفة من الساعة 1 م الواحده مساءآ من تاريخ الحجز و موعد تسليم الغرفة يوم الخروج الساعة 12 م الثانية عشر مساءآ'), small_style))

        # إنشاء المستند مع تذييل في أسفل الصفحة
        def draw_footer(canv, doc_obj):
            try:
                canv.setFont(arabic_font_regular, 12)
            except Exception:
                canv.setFont('Helvetica', 12)
            footer_text = ar('شكرا لاختاريكم فندق قارون')
            text_width = pdfmetrics.stringWidth(footer_text, arabic_font_regular if arabic_font_regular else 'Helvetica', 12)
            page_width, page_height = doc.pagesize
            x = (page_width - text_width) / 2
            y = 35  # 35 نقطة فوق الحافة السفلية
            canv.drawString(x, y, footer_text)

        doc.build(elements, onFirstPage=draw_footer, onLaterPages=draw_footer)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        # إنشاء الاستجابة
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        filename = f"booking_{booking_code}.pdf"
        response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    except Exception as e:
        flash(f'حدث خطأ أثناء إنشاء ملف PDF: {e}', 'error')
        return redirect(url_for('booking.details', id=id))

@booking_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """تعديل الحجز"""
    booking = Booking.query.get_or_404(id)

    # Check if user has permission to edit this booking
    if not current_user.can_edit_booking() and booking.user_id != current_user.id:
        flash('ليس لديك صلاحية لتعديل هذا الحجز', 'danger')
        return redirect(url_for('booking.details', id=id))

    form = BookingForm()

    # إعداد خيارات الغرف
    rooms = Room.query.all()
    room_choices = [('', 'اختر الغرفة...')]
    for r in rooms:
        room_type_display = r.get_room_type_display() if hasattr(r, 'get_room_type_display') else r.room_type
        price_display = f' - {r.price_per_night} جنيه/ليلة' if hasattr(r, 'price_per_night') else ''
        room_choices.append((r.id, f'غرفة {r.room_number} - {room_type_display}{price_display}'))

    form.room_id.choices = room_choices

    if form.validate_on_submit():
        try:
            # التحقق من حالة العميل قبل التعديل
            customer_id = form.customer_id.data
            if customer_id:
                customer = Customer.query.get(customer_id)
                if customer and customer.is_blocked:
                    flash(f'لا يمكن تعديل حجز للعميل {customer.name} - العميل محظور: {customer.block_reason}', 'danger')
                    return render_template('booking/edit.html', form=form, booking=booking, title='تعديل الحجز')
            
            # التحقق من توفر الغرفة أولاً (مع استثناء الحجز الحالي)
            is_available, conflicting_booking = check_room_availability_for_booking(
                form.room_id.data, form.check_in_date.data, form.check_out_date.data, exclude_booking_id=booking.id
            )

            if not is_available:
                room = Room.query.get(form.room_id.data)
                room_number = room.room_number if room else 'غير معروف'
                flash(f'عذراً، الغرفة رقم {room_number} محجوزة بالفعل من {conflicting_booking.check_in_date} إلى {conflicting_booking.check_out_date} للعميل {conflicting_booking.customer.name}', 'error')
                return render_template('booking/edit.html', title=f'تعديل الحجز #{booking.id}', form=form, booking=booking)

            # تحديث بيانات الحجز
            booking.customer_id = form.customer_id.data  # تحديث العميل
            booking.room_id = form.room_id.data
            booking.check_in_date = form.check_in_date.data
            booking.check_out_date = form.check_out_date.data
            booking.occupancy_type = form.occupancy_type.data
            booking.discount_percentage = form.discount_percentage.data or 0
            booking.is_deus = form.is_deus.data
            booking.notes = form.notes.data

            # إعادة حساب السعر
            days = (form.check_out_date.data - form.check_in_date.data).days
            if days <= 0:
                flash('تاريخ المغادرة يجب أن يكون بعد تاريخ الوصول', 'error')
                return render_template('booking/edit.html', title=f'تعديل الحجز #{booking.id}', form=form, booking=booking)

            # أسعار الإقامة الجديدة حسب طلب العميل
            if form.is_deus.data:
                # أسعار الديوز الجديدة
                prices = {'single': 600, 'double': 800, 'triple': 1000}
            else:
                # الأسعار العادية
                prices = {'single': 900, 'double': 1250, 'triple': 1500}
                
            price_per_night = prices.get(form.occupancy_type.data, 900 if not form.is_deus.data else 600)
            base_price = price_per_night * days

            # حساب الضريبة أولاً على المبلغ الأساسي
            tax_percentage = 14.0 if form.include_tax.data else 0.0
            tax_amount = (base_price * tax_percentage) / 100 if form.include_tax.data else 0.0
            total_with_tax = base_price + tax_amount

            # تطبيق الخصم على الإجمالي (شامل الضريبة)
            discount_percentage = form.discount_percentage.data or 0
            discount_amount = form.discount_amount.data or 0
            if discount_amount > 0:
                total_price = total_with_tax - discount_amount
            else:
                discount_amount = (total_with_tax * discount_percentage) / 100
                total_price = total_with_tax - discount_amount
            after_discount = total_price - tax_amount  # للعرض فقط

            # تحديث الأسعار
            booking.base_price = base_price
            booking.tax_percentage = tax_percentage
            booking.tax_amount = tax_amount
            booking.total_price = total_price
            booking.discount_amount = discount_amount
            booking.discount_percentage = discount_percentage

            db.session.commit()

            flash('تم تحديث الحجز بنجاح', 'success')
            return redirect(url_for('booking.details', id=booking.id))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تحديث الحجز: {str(e)}', 'error')

    # تعبئة النموذج بالبيانات الحالية
    if request.method == 'GET':
        # بيانات العميل
        form.customer_id.data = booking.customer_id
        form.customer_search.data = booking.customer.name if booking.customer else ''

        # باقي البيانات
        form.room_id.data = booking.room_id
        form.check_in_date.data = booking.check_in_date
        form.check_out_date.data = booking.check_out_date
        form.occupancy_type.data = booking.occupancy_type
        form.discount_percentage.data = booking.discount_percentage
        form.include_tax.data = (booking.tax_percentage or 0) > 0
        form.is_deus.data = booking.is_deus
        form.notes.data = booking.notes

    return render_template('booking/edit.html', title=f'تعديل الحجز #{booking.id}', form=form, booking=booking)

@booking_bp.route('/<int:id>/check_in', methods=['POST'])
@login_required
def check_in(id):
    """تسجيل دخول العميل"""
    booking = Booking.query.get_or_404(id)

    # التحقق من الصلاحية
    if not current_user.can_check_in_out():
        flash('ليس لديك صلاحية لتسجيل الدخول', 'danger')
        return redirect(url_for('booking.details', id=id))

    # Check if booking can be checked in
    if booking.status != 'confirmed':
        flash('لا يمكن تسجيل الدخول لهذا الحجز في حالته الحالية', 'danger')
        return redirect(url_for('booking.details', id=booking.id))

    from datetime import datetime
    
    booking.status = 'checked_in'
    from hotel.utils.datetime_utils import get_egypt_now_naive
    booking.check_in_time = get_egypt_now_naive()  # تسجيل وقت الدخول الفعلي بتوقيت مصر

    # Update room status
    if hasattr(booking, 'room') and booking.room:
        booking.room.status = 'occupied'

    # إذا كان حجز ديوز، ابدأ العداد (6 ساعات)
    if booking.is_deus and not booking.deus_start_time:
        from datetime import datetime, timedelta
        booking.deus_start_time = datetime.now()
        booking.deus_end_time = booking.deus_start_time + timedelta(hours=6)
        booking.deus_expired = False

    db.session.commit()

    # Log activity
    log_activity(current_user, 'check_in_booking', f'Checked in booking #{booking.id} for customer {booking.customer.name}')

    flash('تم تسجيل الدخول بنجاح', 'success')
    return redirect(url_for('booking.details', id=booking.id))

@booking_bp.route('/<int:id>/check_out', methods=['POST'])
@login_required
def check_out(id):
    """تسجيل خروج العميل"""
    booking = Booking.query.get_or_404(id)

    # التحقق من الصلاحية
    if not current_user.can_check_in_out():
        flash('ليس لديك صلاحية لتسجيل الخروج', 'danger')
        return redirect(url_for('booking.details', id=id))

    # Check if booking can be checked out
    if booking.status != 'checked_in':
        flash('لا يمكن تسجيل الخروج لهذا الحجز في حالته الحالية', 'danger')
        return redirect(url_for('booking.details', id=booking.id))

    from datetime import datetime
    
    booking.status = 'checked_out'
    from hotel.utils.datetime_utils import get_egypt_now_naive
    booking.check_out_time = get_egypt_now_naive()  # تسجيل وقت الخروج الفعلي بتوقيت مصر

    # Update room status
    if hasattr(booking, 'room') and booking.room:
        booking.room.status = 'available'

    # إذا كان حجز ديوز، أنهِ العداد
    if booking.is_deus:
        booking.deus_expired = True

    # Update room status
    update_room_status(booking.room_id)

    db.session.commit()

    # Log activity
    log_activity(current_user, 'check_out_booking', f'Checked out booking #{booking.id} for customer {booking.customer.name}')

    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('booking.details', id=booking.id))

@booking_bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
def cancel(id):
    """
    إلغاء الحجز في أي حالة، مع منطق الاسترجاع:
    - إذا كان الحجز "checked_in": يُسمح بالإلغاء ويتم إنشاء عملية استرجاع (Refund) بقيمة المبلغ المدفوع.
    - في الحالات الأخرى: يتم الإلغاء فقط.
    """
    booking = Booking.query.get_or_404(id)

    # صلاحيات الإلغاء: مدير الحجوزات أو صاحب الحجز
    if not current_user.has_permission('manage_bookings') and booking.user_id != current_user.id:
        flash('ليس لديك صلاحية لإلغاء هذا الحجز', 'danger')
        if current_user.has_permission('admin'):
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('user.dashboard'))

    if booking.status == 'cancelled':
        flash('الحجز ملغى بالفعل', 'warning')
        return redirect(url_for('booking.details', id=booking.id))

    # منطق الاسترجاع عند الإلغاء بعد تسجيل الدخول
    refund_created = False
    refund_amount = 0.0

    try:
        from datetime import datetime

        if booking.status == 'checked_in':
            # احتساب المبلغ المدفوع الفعلي
            booking.update_paid_amount()
            refund_amount = booking.paid_amount or 0.0

            if refund_amount > 0:
                refund_payment = Payment(
                    booking_id=booking.id,
                    amount=-abs(refund_amount),  # قيمة سالبة للاسترجاع
                    payment_type='cash',  # يمكن تعديلها لاحقًا: cash/card/bank_transfer
                    notes='استرجاع تلقائي عند إلغاء الحجز بعد تسجيل الدخول',
                    user_id=current_user.id
                )
                db.session.add(refund_payment)
                refund_created = True

        # إلغاء الحجز وتاريخ الإلغاء
        booking.status = 'cancelled'
        booking.cancelled_at = datetime.utcnow()

        # تحديث المبلغ المدفوع بعد الاسترجاع إن وجد
        booking.update_paid_amount()

        # تحديث حالة الغرفة
        update_room_status(booking.room_id)

        db.session.commit()

        # سجل النشاط
        if refund_created:
            log_activity(current_user, 'cancel_booking_with_refund', f'Cancelled booking #{booking.id} with refund {refund_amount} for customer {booking.customer.name}')
        else:
            log_activity(current_user, 'cancel_booking', f'Cancelled booking #{booking.id} for customer {booking.customer.name}')

        # رسائل للمستخدم
        if refund_created and refund_amount > 0:
            flash(f'تم إلغاء الحجز واسترجاع مبلغ {refund_amount} جنيه للعميل', 'success')
        else:
            flash('تم إلغاء الحجز بنجاح', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء إلغاء الحجز: {str(e)}', 'danger')
        return redirect(url_for('booking.details', id=booking.id))

    # إعادة التوجيه
    if current_user.has_permission('manage_bookings'):
        return redirect(url_for('booking.index'))
    elif current_user.has_permission('admin'):
        return redirect(url_for('admin.dashboard'))
    else:
        return redirect(url_for('user.dashboard'))

@booking_bp.route('/<int:id>/confirm', methods=['POST'])
@login_required
def confirm(id):
    booking = Booking.query.get_or_404(id)

    # التحقق من الصلاحية
    if not current_user.can_edit_booking():
        flash('ليس لديك صلاحية لتأكيد الحجز', 'danger')
        return redirect(url_for('booking.details', id=id))

    if booking.status == 'confirmed':
        flash('الحجز مؤكد بالفعل', 'warning')
        return redirect(url_for('booking.details', id=booking.id))

    if booking.status == 'cancelled':
        flash('لا يمكن تأكيد حجز ملغى', 'danger')
        return redirect(url_for('booking.details', id=booking.id))

    booking.status = 'confirmed'
    db.session.commit()

    log_activity(current_user, 'confirm_booking', f'Confirmed booking #{booking.id} for customer {booking.customer.name}')

    flash('تم تأكيد الحجز بنجاح', 'success')
    return redirect(url_for('booking.details', id=booking.id))
