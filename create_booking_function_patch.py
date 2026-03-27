from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from hotel import db
from hotel.models import Booking, Room, Customer
from hotel.forms.booking import BookingForm

@login_required
def create():
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

            # إنشاء الحجز الجديد
            booking = Booking(
                user_id=current_user.id,
                room_id=room.id,
                customer_id=customer.id,
                check_in_date=form.check_in_date.data,
                check_out_date=form.check_out_date.data,
                occupancy_type=form.occupancy_type.data,
                is_deus=form.is_deus.data,
                base_price=room.price_per_night,
                discount_percentage=form.discount_percentage.data or 0,
                discount_amount=form.discount_amount.data or 0,
                tax_percentage=14.0 if form.include_tax.data else 0.0,
                tax_amount=0.0,
                total_price=0.0,
                paid_amount=0.0,
                notes=form.notes.data
            )
            db.session.add(booking)
            db.session.commit()

            flash('تم إنشاء الحجز بنجاح', 'success')
            return redirect(url_for('booking.details', id=booking.id))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إنشاء الحجز: {e}', 'danger')
            return render_template('booking/create.html', form=form, title='إنشاء حجز جديد')

    return render_template('booking/create.html', form=form, title='إنشاء حجز جديد')
