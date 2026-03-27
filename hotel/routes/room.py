from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import or_, and_

from hotel import db
from hotel.models import Room, Booking, ROOM_TYPE_SINGLE, ROOM_TYPE_DOUBLE, ROOM_TYPE_TRIPLE
from hotel.forms.room import RoomForm
from hotel.utils.decorators import permission_required

room_bp = Blueprint('room', __name__, url_prefix='/rooms')

@room_bp.route('/')
@login_required
def index():
    from hotel.utils.arabic_date import get_arabic_date
    from hotel.models.booking import Booking
    from datetime import date

    today_date = get_arabic_date()
    today = date.today()

    # الحصول على جميع الغرف
    rooms = Room.query.all()

    # إضافة معلومات الحجوزات النشطة لكل غرفة
    for room in rooms:
        # التحقق من وجود حجز نشط لهذه الغرفة اليوم
        # للحساب العادي: confirmed أو checked_in
        # للديوز: فقط checked_in (بعد تسجيل الدخول)
        # التحقق من وجود حجز نشط لهذه الغرفة اليوم
        # الحساب العادي: confirmed أو checked_in
        # الديوز: فقط checked_in (بعد تسجيل الدخول)

        # ابحث عن حجز عادي أولاً
        normal_booking = Booking.query.filter(
            Booking.room_id == room.id,
            Booking.check_in_date <= today,
            Booking.check_out_date > today,
            Booking.is_deus == False,
            Booking.status.in_(['confirmed', 'checked_in'])
        ).first()

        # ابحث عن حجز ديوز مسجل دخول
        deus_booking = Booking.query.filter(
            Booking.room_id == room.id,
            Booking.check_in_date <= today,
            Booking.check_out_date >= today,  # >= بدلاً من > للديوز (نفس اليوم)
            Booking.is_deus == True,
            Booking.status == 'checked_in'
        ).first()

        # اختر الحجز النشط
        active_booking = normal_booking or deus_booking

        # إضافة خاصية للغرفة لمعرفة إذا كانت محجوزة
        room.has_active_booking = active_booking is not None
        room.active_booking_info = active_booking

    # إحصائيات أنواع الغرف
    room_type_stats = {
        'single': len([r for r in rooms if r.room_type == 'single']),
        'double': len([r for r in rooms if r.room_type == 'double']),
        'triple': len([r for r in rooms if r.room_type == 'triple']),
    }

    return render_template('room/index.html',
                         title='قائمة الغرف',
                         rooms=rooms,
                         today_date=today_date,
                         room_type_stats=room_type_stats)

@room_bp.route('/available')
@login_required
def available():
    rooms = Room.query.filter_by(status='available').all()
    return render_template('room/available.html', title='الغرف المتاحة', rooms=rooms)

@room_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('manage_rooms')
def create():
    form = RoomForm()
    if form.validate_on_submit():
        room = Room(
            room_number=form.room_number.data,
            room_type=form.room_type.data,
            price_per_night=form.price_per_night.data,
            capacity=form.capacity.data,
            description=form.description.data
        )
        db.session.add(room)
        db.session.commit()
        flash('تم إضافة الغرفة بنجاح', 'success')
        return redirect(url_for('room.index'))
    
    return render_template('room/create.html', title='إضافة غرفة جديدة', form=form)

@room_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('manage_rooms')
def edit(id):
    room = Room.query.get_or_404(id)
    form = RoomForm(obj=room)

    # تعيين الكائن الحالي للنموذج للتحقق من التحديث
    form._obj = room

    if form.validate_on_submit():
        room.room_number = form.room_number.data
        room.room_type = form.room_type.data
        room.price_per_night = form.price_per_night.data
        room.capacity = form.capacity.data
        room.description = form.description.data

        db.session.commit()
        flash('تم تحديث بيانات الغرفة بنجاح', 'success')
        return redirect(url_for('room.index'))

    return render_template('room/edit.html', title='تعديل بيانات الغرفة', form=form, room=room)

@room_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('manage_rooms')
def delete(id):
    room = Room.query.get_or_404(id)
    
    # Check if room has any bookings
    if room.bookings.count() > 0:
        flash('لا يمكن حذف الغرفة لأنها مرتبطة بحجوزات', 'danger')
        return redirect(url_for('room.index'))
    
    db.session.delete(room)
    db.session.commit()
    flash('تم حذف الغرفة بنجاح', 'success')
    return redirect(url_for('room.index'))

@room_bp.route('/<int:id>')
@login_required
def details(id):
    from hotel.models.booking import Booking
    from datetime import date
    from sqlalchemy import or_

    room = Room.query.get_or_404(id)
    today = date.today()

    # التحقق من وجود حجز نشط لهذه الغرفة اليوم
    try:
        active_booking = Booking.query.filter(
            Booking.room_id == room.id,
            Booking.check_in_date <= today,
            Booking.check_out_date > today,
            or_(
                Booking.status == 'confirmed',
                Booking.status == 'checked_in'
            )
        ).first()
        
        # Debugging
        print(f"Active booking found: {active_booking is not None}")
        if active_booking:
            print(f"Booking ID: {active_booking.id}, Status: {active_booking.status}")
            print(f"Check-in: {active_booking.check_in_date}, Check-out: {active_booking.check_out_date}")

        # إضافة معلومات الحجز النشط للغرفة
        active_booking_info = None
        if active_booking:
            customer_name = 'عميل غير معروف'
            customer_id = 'N/A'
            
            if hasattr(active_booking, 'customer') and active_booking.customer:
                customer_name = active_booking.customer.name or 'عميل غير معروف'
                customer_id = active_booking.customer.id_number or 'N/A'
            
            active_booking_info = {
                'id': active_booking.id,
                'customer': {
                    'name': customer_name,
                    'id_number': customer_id
                },
                'check_in_date': active_booking.check_in_date,
                'check_out_date': active_booking.check_out_date,
                'status': active_booking.status,
                'created_at': active_booking.created_at if hasattr(active_booking, 'created_at') else None,
                'total_price': getattr(active_booking, 'total_price', 0) or 0
            }
            
            print(f"Booking info prepared: {active_booking_info}")
            
    except Exception as e:
        print(f"Error in room details: {str(e)}")
        active_booking_info = None

    return render_template('room/details.html', 
                         title=f'تفاصيل الغرفة {room.room_number}', 
                         room=room,
                         active_booking_info=active_booking_info)