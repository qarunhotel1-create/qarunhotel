from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from sqlalchemy import or_, and_

from hotel import db
from hotel.models import User, Room, Booking, Customer, Payment, Permission, ActivityLog
from hotel.utils.decorators import permission_required
from hotel.forms.admin import BookingSearchForm, UserForm, EditUserForm
from hotel.utils.activity_logger import log_activity

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@permission_required('dashboard')
def dashboard():
    from datetime import date

    # Get statistics for the dashboard
    total_rooms = Room.query.count()
    available_rooms = Room.query.filter_by(status='available').count()
    total_bookings = Booking.query.count()
    active_bookings = Booking.query.filter(Booking.status.in_(['pending', 'confirmed', 'checked_in'])).count()
    total_customers = Customer.query.count()

    # Get recent bookings
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()

    # تحديث حالة الغرف تلقائياً
    try:
        from hotel.utils.room_status_updater import update_room_statuses
        update_room_statuses()
    except Exception as e:
        print(f"خطأ في تحديث حالة الغرف: {e}")

    # Get all rooms with their current status for today
    today = date.today()

    from hotel.utils.arabic_date import get_arabic_date
    today_formatted = get_arabic_date(today)

    all_rooms = Room.query.order_by(Room.room_number).all()

    # Create room status map for today
    rooms_status = []
    for room in all_rooms:
        # Check if room has active booking for today
        # للحساب العادي: confirmed أو checked_in
        # للديوز: فقط checked_in (بعد تسجيل الدخول)
        # Check if room has active booking for today
        # الحساب العادي: confirmed أو checked_in
        # الديوز: فقط checked_in (بعد تسجيل الدخول)

        # ابحث عن حجز عادي أولاً
        normal_booking = Booking.query.filter(
            Booking.room_id == room.id,
            Booking.check_in_date <= today,
            Booking.check_out_date >= today,
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



        # تحديد نوع الحجز ولونه
        room_class = 'available'
        status_text = 'فارغة'
        status_icon = 'fas fa-door-open'

        if active_booking:
            if active_booking.status == 'checked_in':
                room_class = 'occupied'  # مسجل الدخول = أحمر
            else:
                room_class = 'reserved'  # مؤكد فقط = أصفر
                
            if active_booking.is_deus:
                status_text = 'ديوز نشط'
                status_icon = 'fas fa-clock'  # أيقونة مختلفة للديوز
            else:
                if active_booking.status == 'checked_in':
                    status_text = 'مسجل الدخول'
                else:
                    status_text = 'محجوزة'
                status_icon = 'fas fa-user'

        room_info = {
            'room': room,
            'is_occupied': active_booking is not None,
            'booking': active_booking,
            'status_class': room_class,
            'status_text': status_text,
            'status_icon': status_icon
        }
        rooms_status.append(room_info)

    # Count occupied and available rooms for today
    occupied_today = sum(1 for room in rooms_status if room['is_occupied'])
    available_today = total_rooms - occupied_today

    return render_template('admin/dashboard.html',
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

@admin_bp.route('/update-room-status')
@login_required
@permission_required('admin')
def update_room_status():
    """تحديث حالة الغرف بناءً على الحجوزات النشطة"""
    from datetime import date

    today = date.today()
    rooms = Room.query.all()
    updated_count = 0

    # تطبيق حد 1 ظهرًا بتوقيت مصر
    from hotel.utils.datetime_utils import get_egypt_now
    now = get_egypt_now()
    cutoff_passed = now.hour >= 13

    for room in rooms:
        # التحقق من وجود حجز نشط لهذه الغرفة اليوم
        filters = [
            Booking.room_id == room.id,
            Booking.check_in_date <= today,
            Booking.status.in_(['confirmed', 'checked_in'])
        ]
        if cutoff_passed:
            filters.append(Booking.check_out_date > today)
        else:
            filters.append(Booking.check_out_date >= today)

        active_booking = Booking.query.filter(*filters).first()

        # تحديث حالة الغرفة (إلا إذا كانت في صيانة)
        old_status = room.status
        if room.status != 'maintenance':
            if active_booking:
                room.status = 'occupied'
            else:
                room.status = 'available'

        if old_status != room.status:
            updated_count += 1

    db.session.commit()
    log_activity(current_user, 'update_room_status', f'Updated status for {updated_count} rooms')

    flash(f'تم تحديث حالة {updated_count} غرفة', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/users')
@login_required
@permission_required('manage_users')
def users():
    users = User.query.filter_by(is_guest=False).all()
    return render_template('admin/users.html', title='إدارة المستخدمين', users=users)

@admin_bp.route('/create-user', methods=['GET', 'POST'])
@login_required
@permission_required('manage_users')
def create_user():
    form = UserForm()
    if form.validate_on_submit():
        permissions = Permission.query.filter(Permission.id.in_(form.permissions.data)).all()
        user = User(
            username=form.username.data,
            password=form.password.data,
            full_name=form.full_name.data,
            permissions=permissions
        )
        db.session.add(user)
        log_activity(current_user, 'create_user', f'Created user {user.username}')
        db.session.commit()
        flash('تم إنشاء المستخدم بنجاح', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/create_user.html', title='إنشاء مستخدم جديد', form=form)

@admin_bp.route('/create-admin', methods=['GET', 'POST'])
@login_required
@permission_required('manage_users')
def create_admin():
    """إنشاء مستخدم مسؤول جديد"""
    form = UserForm()
    if form.validate_on_submit():
        # الحصول على صلاحية المسؤول
        admin_permission = Permission.query.filter_by(name='admin').first()
        if not admin_permission:
            flash('خطأ: صلاحية المسؤول غير موجودة', 'danger')
            return redirect(url_for('admin.users'))

        user = User(
            username=form.username.data,
            password=form.password.data,
            full_name=form.full_name.data,
            permissions=[admin_permission]
        )
        db.session.add(user)
        log_activity(current_user, 'create_admin', f'Created admin user {user.username}')
        db.session.commit()
        flash('تم إنشاء حساب المسؤول بنجاح', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/create_admin.html', title='إنشاء حساب مسؤول', form=form)

@admin_bp.route('/edit-user/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required('manage_users')
def edit_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('لا يمكنك تعديل حسابك الخاص من هنا', 'warning')
        return redirect(url_for('admin.users'))

    form = EditUserForm(user.username)
    if form.validate_on_submit():
        user.username = form.username.data
        user.full_name = form.full_name.data
        user.permissions = Permission.query.filter(Permission.id.in_(form.permissions.data)).all()
        if form.password.data:
            user.set_password(form.password.data)
        log_activity(current_user, 'edit_user', f'Edited user {user.username}')
        db.session.commit()
        flash(f'تم تحديث بيانات المستخدم {user.username} بنجاح', 'success')
        return redirect(url_for('admin.users'))

    elif request.method == 'GET':
        form.username.data = user.username
        form.full_name.data = user.full_name
        form.permissions.data = [p.id for p in user.permissions]

    return render_template('admin/edit_user.html', title='تعديل المستخدم', form=form, user=user)

@admin_bp.route('/delete-user/<int:id>', methods=['POST'])
@login_required
@permission_required('manage_users')
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('لا يمكنك حذف حسابك الخاص', 'danger')
        return redirect(url_for('admin.users'))

    # Reassign bookings to the current user or a default admin
    # This is a simple approach; a more complex system might have a dedicated user for this
    for booking in user.bookings:
        booking.user_id = current_user.id

    db.session.delete(user)
    log_activity(current_user, 'delete_user', f'Deleted user {user.username}')
    db.session.commit()
    flash('تم حذف المستخدم بنجاح', 'success')
    return redirect(url_for('admin.users'))





@admin_bp.route('/activity-log')
@login_required
@permission_required('view_reports')
def activity_log():
    page = request.args.get('page', 1, type=int)
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).paginate(page=page, per_page=20)
    return render_template('admin/activity_log.html', title='سجل النشاطات', logs=logs)

@admin_bp.route('/search-bookings')
@login_required
@permission_required('manage_bookings')
def search_bookings():
    """البحث عن الحجوزات"""
    form = BookingSearchForm()
    bookings = []
    search_query = None

    # التحقق من طلب AJAX
    is_ajax = request.args.get('ajax') == '1'

    if request.method == 'POST' and form.validate_on_submit():
        search_query = form.search_query.data.strip()
    elif request.method == 'GET' and request.args.get('q'):
        search_query = request.args.get('q').strip()

    if search_query:
        try:
            # البحث الدقيق والمحدد
            bookings_query = Booking.query.join(Customer).join(Room)
            bookings = []

            # 1. البحث برقم الحجز بصيغة السنة/الرقم (يدعم أيضاً الشرطة للتوافق)
            import re
            yearly_match = re.match(r'^(\d{4})[-/](\d{1,4})$', search_query)
            if yearly_match:
                y = int(yearly_match.group(1))
                s = int(yearly_match.group(2))
                exact_booking = bookings_query.filter(Booking.booking_year == y, Booking.year_seq == s).first()
                if exact_booking:
                    bookings = [exact_booking]
                else:
                    bookings = []
            elif search_query.isdigit():
                booking_id = int(search_query)
                bookings = []
                
                # 1. البحث كترقيم سنوي (الأولوية كما طلب المستخدم لعرض كل السنوات)
                seq_matches = bookings_query.filter(Booking.year_seq == booking_id).order_by(Booking.created_at.desc()).all()
                if seq_matches:
                    bookings.extend(seq_matches)
                
                # 2. البحث برقم المعرف الفريد (ID)
                id_match = bookings_query.filter(Booking.id == booking_id).first()
                if id_match:
                    # التأكد من عدم التكرار
                    exists = False
                    for b in bookings:
                        if b.id == id_match.id:
                            exists = True
                            break
                    if not exists:
                        bookings.append(id_match)
                
                # 3. إذا لم يوجد أي نتائج رقمية، ابحث في الهواتف وأرقام الهوية
                if not bookings:
                    bookings = bookings_query.filter(
                        or_(
                            Customer.phone == search_query,
                            Customer.id_number == search_query,
                            Room.room_number == search_query
                        )
                    ).order_by(Booking.created_at.desc()).all()
            else:
                # 2. البحث النصي الدقيق
                # أولاً: البحث بالاسم الكامل
                exact_name_bookings = bookings_query.filter(
                    Customer.name.ilike(f'{search_query}')
                ).order_by(Booking.created_at.desc()).all()

                if exact_name_bookings:
                    bookings = exact_name_bookings
                else:
                    # ثانياً: البحث بجزء من الاسم (إذا كان أكثر من حرفين)
                    if len(search_query) >= 2:
                        partial_name_bookings = bookings_query.filter(
                            Customer.name.ilike(f'%{search_query}%')
                        ).order_by(Booking.created_at.desc()).all()

                        if partial_name_bookings:
                            bookings = partial_name_bookings
                        else:
                            # ثالثاً: البحث في الهاتف ورقم الهوية
                            bookings = bookings_query.filter(
                                or_(
                                    Customer.phone.ilike(f'%{search_query}%'),
                                    Customer.id_number.ilike(f'%{search_query}%')
                                )
                            ).order_by(Booking.created_at.desc()).all()

            # إذا كان طلب AJAX، إرجاع JSON
            if is_ajax:
                results = []
                for booking in bookings:
                    try:
                        results.append({
                            'id': booking.id,
                            'booking_code': booking.booking_code, 'booking_year': booking.booking_year, 'year_seq': booking.year_seq,
                            'customer_name': booking.customer.name,
                            'customer_phone': booking.customer.phone or '',
                            'customer_id_number': booking.customer.id_number or '',
                            'room_number': booking.room.room_number,
                            'check_in': booking.check_in_date.strftime('%Y-%m-%d') if booking.check_in_date else '',
                            'check_out': booking.check_out_date.strftime('%Y-%m-%d') if booking.check_out_date else '',
                            'status': booking.status,
                            'status_display': booking.get_status_display(),
                            'total_price': float(booking.total_price or 0),
                            'is_deus': booking.is_deus,
                            'url': url_for('booking.details', id=booking.id)
                        })
                    except Exception as e:
                        print(f"خطأ في معالجة الحجز {booking.id}: {e}")
                        continue

                return jsonify({
                    'success': True,
                    'count': len(results),
                    'results': results,
                    'query': search_query
                })
        except Exception as e:
            if is_ajax:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'count': 0,
                    'results': []
                })
            flash(f'حدث خطأ في البحث: {str(e)}', 'error')
            bookings = []

    return render_template('admin/search_bookings.html',
                         title='البحث عن الحجوزات',
                         form=form,
                         bookings=bookings,
                         search_query=search_query)

@admin_bp.route('/permissions-test')
@login_required
def permissions_test():
    """صفحة اختبار الصلاحيات"""
    return render_template('admin/permissions_test.html', title='اختبار الصلاحيات')

@admin_bp.route('/permissions-comparison')
@login_required
def permissions_comparison():
    """صفحة مقارنة الصلاحيات"""
    return render_template('admin/permissions_comparison.html', title='مقارنة الصلاحيات')

@admin_bp.route('/create-test-user')
@login_required
@permission_required('manage_users')
def create_test_user():
    """إنشاء مستخدم تجريبي مع صلاحيات الحجوزات"""
    # التحقق من وجود المستخدم التجريبي
    test_user = User.query.filter_by(username='test_user').first()
    if test_user:
        flash('المستخدم التجريبي موجود بالفعل: test_user / test123', 'info')
        return redirect(url_for('admin.users'))

    # الحصول على الصلاحيات المطلوبة
    permissions_needed = [
        'manage_bookings', 'manage_payments', 'manage_customers',
        'create_booking', 'edit_booking', 'check_in_out',
        'add_payment', 'edit_payment', 'view_reports'
    ]

    permissions = Permission.query.filter(Permission.name.in_(permissions_needed)).all()

    # إنشاء المستخدم التجريبي
    test_user = User(
        username='test_user',
        password='test123',
        full_name='مستخدم تجريبي - موظف استقبال',
        permissions=permissions
    )

    db.session.add(test_user)
    log_activity(current_user, 'create_user', f'Created test user: {test_user.username}')
    db.session.commit()

    flash(f'تم إنشاء المستخدم التجريبي بنجاح!<br>اسم المستخدم: test_user<br>كلمة المرور: test123<br>الصلاحيات: {len(permissions)} صلاحية', 'success')
    return redirect(url_for('admin.users'))
