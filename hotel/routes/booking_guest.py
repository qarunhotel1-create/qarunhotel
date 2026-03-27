from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import and_

from hotel import db
from hotel.models import Booking, Customer, BookingGuest
from hotel.forms.booking_guest import AddExistingGuestForm, AddNewGuestForm
from hotel.utils.decorators import permission_required
from hotel.utils.activity_logger import log_activity

booking_guest_bp = Blueprint('booking_guest', __name__, url_prefix='/booking-guest')

@booking_guest_bp.route('/<int:booking_id>/manage')
@login_required
@permission_required('manage_bookings')
def manage_guests(booking_id):
    """إدارة المرافقين للحجز"""
    booking = Booking.query.get_or_404(booking_id)
    
    # جلب المرافقين النشطين
    active_guests = BookingGuest.query.filter_by(
        booking_id=booking_id,
        is_active=True
    ).all()
    
    # جلب المرافقين المحذوفين
    removed_guests = BookingGuest.query.filter_by(
        booking_id=booking_id,
        is_active=False
    ).all()
    
    # حساب السعة
    room_capacity = booking.room.capacity if hasattr(booking.room, 'capacity') else 4
    current_guests_count = len(active_guests) + 1  # +1 للعميل الأساسي
    available_capacity = room_capacity - current_guests_count
    
    return render_template('booking_guest/manage_guests.html',
                         title=f'إدارة مرافقي الحجز #{booking.id}',
                         booking=booking,
                         active_guests=active_guests,
                         removed_guests=removed_guests,
                         room_capacity=room_capacity,
                         current_guests_count=current_guests_count,
                         available_capacity=available_capacity)

@booking_guest_bp.route('/<int:booking_id>/add-existing', methods=['GET', 'POST'])
@login_required
@permission_required('manage_bookings')
def add_existing_guest_form(booking_id):
    """إضافة عميل موجود كمرافق"""
    booking = Booking.query.get_or_404(booking_id)
    form = AddExistingGuestForm()

    # إذا تم تمرير customer_id في URL، قم بتعيينه
    customer_id = request.args.get('customer_id', type=int)
    selected_customer = None

    if customer_id and request.method == 'GET':
        selected_customer = Customer.query.get(customer_id)
        if selected_customer:
            form.customer_id.data = customer_id
            form.customer_search.data = selected_customer.name
    
    if form.validate_on_submit():
        try:
            customer_id = int(form.customer_id.data)
            customer = Customer.query.get_or_404(customer_id)

            # التحقق من أن العميل ليس هو العميل الأساسي للحجز
            if booking.customer_id == customer_id:
                flash(f'العميل {customer.name} هو العميل الأساسي للحجز ولا يمكن إضافته كمرافق', 'error')
                return render_template('booking_guest/add_existing_guest.html',
                                     title=f'إضافة مرافق للحجز #{booking.id}',
                                     form=form, booking=booking, selected_customer=customer)

            # التحقق من عدم وجود المرافق مسبقاً
            existing_guest = BookingGuest.query.filter_by(
                booking_id=booking_id,
                customer_id=customer_id,
                is_active=True
            ).first()

            if existing_guest:
                flash(f'العميل {customer.name} موجود بالفعل كمرافق في هذا الحجز', 'warning')
                return render_template('booking_guest/add_existing_guest.html',
                                     title=f'إضافة مرافق للحجز #{booking.id}',
                                     form=form, booking=booking, selected_customer=customer)
            
            # إضافة المرافق
            guest = BookingGuest(
                booking_id=booking_id,
                customer_id=customer_id,
                guest_type=form.guest_type.data,
                relationship=form.relationship.data,
                notes=form.notes.data,
                added_by_user_id=current_user.id
            )
            
            db.session.add(guest)
            db.session.commit()
            
            # تسجيل النشاط
            log_activity(current_user, 'add_booking_guest',
                        f'Added guest {customer.name} to booking #{booking_id}')

            flash(f'تم إضافة {customer.name} كمرافق بنجاح', 'success')
            return redirect(url_for('booking_guest.manage_guests', booking_id=booking_id))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة المرافق: {str(e)}', 'error')

    return render_template('booking_guest/add_existing_guest.html',
                         title=f'إضافة مرافق للحجز #{booking.id}',
                         form=form, booking=booking, selected_customer=selected_customer)

@booking_guest_bp.route('/<int:booking_id>/add-existing-quick', methods=['GET', 'POST'])
@login_required
@permission_required('manage_bookings')
def add_existing_guest_quick(booking_id):
    """إضافة عميل موجود كمرافق بشكل سريع"""
    booking = Booking.query.get_or_404(booking_id)

    # دعم GET و POST
    if request.method == 'GET':
        customer_id = request.args.get('customer_id', type=int)
    else:
        customer_id = request.form.get('customer_id', type=int)

    if not customer_id:
        flash('لم يتم تحديد العميل', 'error')
        return redirect(url_for('booking_guest.manage_guests', booking_id=booking_id))

    try:
        customer = Customer.query.get_or_404(customer_id)

        # التحقق من أن العميل ليس هو العميل الأساسي للحجز
        if booking.customer_id == customer_id:
            flash(f'العميل {customer.name} هو العميل الأساسي للحجز ولا يمكن إضافته كمرافق', 'error')
            return redirect(url_for('booking_guest.manage_guests', booking_id=booking_id))

        # التحقق من عدم وجود المرافق مسبقاً
        existing_guest = BookingGuest.query.filter_by(
            booking_id=booking_id,
            customer_id=customer_id,
            is_active=True
        ).first()

        if existing_guest:
            flash(f'العميل {customer.name} موجود بالفعل كمرافق في هذا الحجز', 'warning')
            return redirect(url_for('booking_guest.manage_guests', booking_id=booking_id))

        # إضافة المرافق بقيم افتراضية
        guest = BookingGuest(
            booking_id=booking_id,
            customer_id=customer_id,
            guest_type='companion',  # نوع افتراضي
            relationship='',  # يمكن تعديلها لاحقاً
            notes='تم إضافته من قائمة العملاء المسجلين',
            added_by_user_id=current_user.id
        )

        db.session.add(guest)
        db.session.commit()

        # تسجيل النشاط
        log_activity(current_user, 'add_booking_guest_quick',
                    f'Added guest {customer.name} to booking #{booking_id} quickly')

        flash(f'تم إضافة {customer.name} كمرافق بنجاح', 'success')
        return redirect(url_for('booking_guest.manage_guests', booking_id=booking_id))

    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء إضافة المرافق: {str(e)}', 'error')
        return redirect(url_for('booking_guest.manage_guests', booking_id=booking_id))

@booking_guest_bp.route('/<int:booking_id>/add-new', methods=['GET', 'POST'])
@login_required
@permission_required('manage_bookings')
def add_new_guest_form(booking_id):
    """إضافة عميل جديد كمرافق"""
    booking = Booking.query.get_or_404(booking_id)
    form = AddNewGuestForm()
    
    if form.validate_on_submit():
        try:
            # إنشاء عميل جديد
            customer = Customer(
                name=form.name.data,
                id_number=form.national_id.data,  # استخدام national_id
                phone=form.phone.data,
                email=form.email.data,
                address=form.address.data,
                nationality=form.nationality.data
            )
            
            db.session.add(customer)
            db.session.flush()  # للحصول على ID العميل
            
            # إضافة المرافق
            guest = BookingGuest(
                booking_id=booking_id,
                customer_id=customer.id,
                guest_type=form.guest_type.data,
                relationship=form.relationship.data,
                notes=form.notes.data,
                added_by_user_id=current_user.id
            )
            
            db.session.add(guest)
            db.session.commit()
            
            # تسجيل النشاط
            log_activity(current_user, 'add_new_booking_guest', 
                        f'Added new guest {customer.name} to booking #{booking_id}')
            
            flash('تم إضافة العميل الجديد كمرافق بنجاح', 'success')
            return redirect(url_for('booking_guest.manage_guests', booking_id=booking_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة العميل الجديد: {str(e)}', 'error')
    
    return render_template('booking_guest/add_new_guest.html',
                         title=f'إضافة عميل جديد للحجز #{booking.id}',
                         form=form, booking=booking)

@booking_guest_bp.route('/remove/<int:guest_id>', methods=['GET', 'POST'])
@login_required
@permission_required('manage_bookings')
def remove_guest(guest_id):
    """إزالة مرافق"""
    guest = BookingGuest.query.get_or_404(guest_id)
    
    try:
        guest.is_active = False
        guest.removed_by_user_id = current_user.id
        guest.removed_by = current_user.id  # الحقل الجديد
        guest.removed_time = datetime.now()
        guest.removed_date = datetime.now()  # الحقل الجديد
        
        db.session.commit()
        
        # تسجيل النشاط
        log_activity(current_user, 'remove_booking_guest', 
                    f'Removed guest {guest.customer.name} from booking #{guest.booking_id}')
        
        flash('تم إزالة المرافق بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء إزالة المرافق: {str(e)}', 'error')
    
    return redirect(url_for('booking_guest.manage_guests', booking_id=guest.booking_id))

@booking_guest_bp.route('/reactivate/<int:guest_id>')
@login_required
@permission_required('manage_bookings')
def reactivate_guest(guest_id):
    """إعادة تفعيل مرافق"""
    guest = BookingGuest.query.get_or_404(guest_id)
    
    try:
        guest.is_active = True
        guest.removed_by_user_id = None
        guest.removed_time = None
        
        db.session.commit()
        
        # تسجيل النشاط
        log_activity(current_user, 'reactivate_booking_guest', 
                    f'Reactivated guest {guest.customer.name} for booking #{guest.booking_id}')
        
        flash('تم إعادة تفعيل المرافق بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء إعادة تفعيل المرافق: {str(e)}', 'error')
    
    return redirect(url_for('booking_guest.manage_guests', booking_id=guest.booking_id))

@booking_guest_bp.route('/api/search-customers')
@login_required
def search_customers():
    """البحث عن العملاء للمرافقين"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify({'customers': []})
    
    customers = Customer.query.filter(
        Customer.name.contains(query) |
        Customer.id_number.contains(query) |
        Customer.phone.contains(query)
    ).limit(10).all()
    
    results = []
    for customer in customers:
        results.append({
            'id': customer.id,
            'name': customer.name,
            'id_number': customer.id_number,
            'phone': customer.phone or ''
        })
    
    return jsonify({'customers': results})

@booking_guest_bp.route('/api/room-capacity/<int:booking_id>')
@login_required
def room_capacity_api(booking_id):
    """API لجلب معلومات سعة الغرفة"""
    booking = Booking.query.get_or_404(booking_id)
    
    active_guests_count = BookingGuest.query.filter_by(
        booking_id=booking_id,
        is_active=True
    ).count()
    
    room_capacity = booking.room.capacity if hasattr(booking.room, 'capacity') else 4
    current_guests_count = active_guests_count + 1  # +1 للعميل الأساسي
    available_capacity = room_capacity - current_guests_count
    
    return jsonify({
        'success': True,
        'room_capacity': room_capacity,
        'current_guests_count': current_guests_count,
        'available_capacity': available_capacity
    })
