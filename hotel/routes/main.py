from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required
from datetime import date
from hotel import db
from hotel.models import Room, Booking, Customer, Payment
from hotel.utils.decorators import permission_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.has_permission('admin'):
            return redirect(url_for('admin.dashboard'))
        else:
            # توجيه المستخدمين العاديين إلى لوحة التحكم الخاصة بهم
            return redirect(url_for('user.dashboard'))
    # غير مسجل: توجيه مباشر لصفحة تسجيل الدخول
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
@permission_required('dashboard')
def user_dashboard():
    """لوحة تحكم المستخدمين مع خريطة الغرف"""

    # Get statistics for the dashboard
    total_rooms = Room.query.count()
    available_rooms = Room.query.filter_by(status='available').count()
    total_bookings = Booking.query.count()
    active_bookings = Booking.query.filter(Booking.status.in_(['pending', 'confirmed', 'checked_in'])).count()
    total_customers = Customer.query.count()

    # Get recent bookings
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()

    # Get all rooms with their current status for today
    today = date.today()
    today_formatted = today.strftime('%Y-%m-%d')

    all_rooms = Room.query.order_by(Room.room_number).all()

    # Create room status map for today (عرض فقط وفق أوقات الفندق)
    from hotel.utils.datetime_utils import get_egypt_now
    now = get_egypt_now()
    after_noon_12 = now.hour >= 12   # نهاية اليوم 12 PM (تشيك-آوت)
    after_checkin_1 = now.hour >= 13 # بداية اليوم 1 PM (تشيك-إن)

    rooms_status = []
    for room in all_rooms:
        # 1) حجز نشط فعلياً (checked_in) ما زال داخل الإقامة
        checked_in_booking = Booking.query.filter(
            Booking.room_id == room.id,
            Booking.status == 'checked_in',
            Booking.check_in_date <= today
        ).order_by(Booking.id.desc()).first()

        active_checked_in = None
        cleaning_booking = None
        if checked_in_booking:
            # ما زال داخل الإقامة إذا كان تاريخ الخروج > اليوم
            # أو لو الخروج اليوم لكن قبل 12 PM
            if checked_in_booking.check_out_date > today:
                active_checked_in = checked_in_booking
            elif checked_in_booking.check_out_date == today:
                if not after_noon_12:
                    active_checked_in = checked_in_booking
                else:
                    # بعد 12 PM نعرض "تنظيف"
                    cleaning_booking = checked_in_booking

        # 2) حجز مؤكد لليوم (ولم يتم التشيك-إن بعد)
        confirmed_today_booking = Booking.query.filter(
            Booking.room_id == room.id,
            Booking.is_deus == False,
            Booking.status == 'confirmed',
            Booking.check_in_date <= today,
            Booking.check_out_date >= today
        ).order_by(Booking.id.desc()).first()

        # 3) ديوز نشط (يُعرض فقط عند التشيك-إن)
        deus_checked_in = Booking.query.filter(
            Booking.room_id == room.id,
            Booking.is_deus == True,
            Booking.status == 'checked_in',
            Booking.check_in_date <= today
        ).order_by(Booking.id.desc()).first()

        # تحديد الحالة المعروضة
        display_booking = None
        status_class = 'available'
        status_text = 'فارغة'
        status_icon = 'fas fa-door-open text-success'

        if active_checked_in or deus_checked_in:
            display_booking = active_checked_in or deus_checked_in
            status_class = 'occupied'
            status_text = 'مشغولة'
            status_icon = 'fas fa-user text-danger'
        elif after_noon_12 and confirmed_today_booking:
            # بعد 12 PM يتم التحويل تلقائياً إلى حجز العميل التالي إن وجد
            display_booking = confirmed_today_booking
            status_class = 'reserved'
            status_text = 'محجوزة'
            status_icon = 'fas fa-calendar text-warning'
        elif cleaning_booking and after_noon_12:
            # بعد 12 PM نعرض "تنظيف" إذا لم يوجد حجز لاحق اليوم
            display_booking = cleaning_booking
            status_class = 'available'  # يظل لون متاح (عرض فقط)
            status_text = 'تنظيف'
            status_icon = 'fas fa-broom text-warning'
        elif confirmed_today_booking and after_checkin_1:
            # بعد 1 PM تظهر كـ "محجوزة" لليوم إذا لم يتم التشيك-إن بعد
            display_booking = confirmed_today_booking
            status_class = 'reserved'
            status_text = 'محجوزة'
            status_icon = 'fas fa-calendar text-warning'
        else:
            # قبل 1 PM تبقى الغرفة "فارغة" حتى لو لديها حجز لليوم (عرض فقط)
            pass

        room_info = {
            'room': room,
            'is_occupied': status_class in ['occupied', 'reserved'] and display_booking is not None and not (status_text == 'تنظيف'),
            'booking': display_booking,
            'status_class': status_class,
            'status_text': status_text,
            'status_icon': status_icon
        }

        rooms_status.append(room_info)

    # Count occupied and available rooms لعرض اليوم
    occupied_today = sum(1 for r in rooms_status if r['is_occupied'])
    available_today = total_rooms - occupied_today

    return render_template('main/user_dashboard.html',
                          title='لوحة التحكم',
                          total_rooms=total_rooms,
                          available_rooms=available_rooms,
                          total_bookings=total_bookings,
                          active_bookings=active_bookings,
                          total_customers=total_customers,
                          recent_bookings=recent_bookings,
                          rooms_status=rooms_status,
                          occupied_today=occupied_today,
                          available_today=available_today,
                          today=today,
                          today_formatted=today_formatted)
